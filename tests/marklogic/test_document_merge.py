"""MarkLogic integration tests for Document.merge_into."""

import contextlib
import json

import pytest
from lxml import etree

from caselawclient.Client import get_multipart_strings_from_marklogic_response
from caselawclient.client_helpers import document_from_xml
from caselawclient.content_hash import get_hash_from_document
from caselawclient.errors import MarklogicAPIError
from caselawclient.models.documents.body import DocumentBody
from caselawclient.models.documents.exceptions import DocumentMergeNotPossibleError
from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataStringValue
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.versions import VersionType
from caselawclient.models.utilities import extract_version
from caselawclient.types import DocumentURIString
from marklogic_harness.corpus import (
    DOCUMENTS_DIR,
    INSERT_MANAGED_DOCUMENT_XQY,
    TEST_METADATA_WRITES_URI,
    _version_annotation_json,
)

pytestmark = [pytest.mark.marklogic, pytest.mark.write]

TARGET_URI = DocumentURIString("test/merge_target")
SOURCE_URI = DocumentURIString("test/merge_source")


NSMAP = {
    "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "uk": "https://caselaw.nationalarchives.gov.uk/akn",
}


def _different_valid_judgment_xml() -> str:
    """The metadata_writes fixture with altered text and a matching content hash, so it can be saved as a Judgment."""
    root = etree.fromstring((DOCUMENTS_DIR / "metadata_writes.xml").read_bytes())
    root.xpath("//akn:p", namespaces=NSMAP)[0].text = "Content of the document being merged"
    root.xpath("//uk:hash", namespaces=NSMAP)[0].text = get_hash_from_document(etree.tostring(root))
    return etree.tostring(root).decode()


def _insert_source(client, uri) -> None:
    variables = {
        "uri": uri.as_marklogic(),
        "document_xml": _different_valid_judgment_xml(),
        "annotation": _version_annotation_json(client, "source upload"),
        "type_collection": "judgment",
    }
    client.eval(str(INSERT_MANAGED_DOCUMENT_XQY), vars=json.dumps(variables))


def _version_count(client, uri) -> int:
    return len(get_multipart_strings_from_marklogic_response(client.list_judgment_versions(uri)))


def _remove(client, uri) -> None:
    if client.document_exists(uri):
        for action in (client.checkin_judgment, client.break_checkout):
            with contextlib.suppress(MarklogicAPIError):
                action(uri)
        client.delete_judgment(uri)


@pytest.fixture
def s3_calls(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(
        "caselawclient.models.documents.copy_assets", lambda *args, **kwargs: calls.append(("copy", args, kwargs))
    )
    monkeypatch.setattr(
        "caselawclient.models.documents.delete_documents_from_private_bucket", lambda uri: calls.append(("delete", uri))
    )
    return calls


@pytest.fixture
def merge_target(marklogic_api_client):
    """A throwaway copy of the metadata_writes judgment, to be merged into."""
    _remove(marklogic_api_client, TARGET_URI)
    _remove(marklogic_api_client, SOURCE_URI)
    marklogic_api_client.copy_document(TEST_METADATA_WRITES_URI, TARGET_URI)
    marklogic_api_client.set_published(TARGET_URI, False)
    yield marklogic_api_client.get_document_by_uri(TARGET_URI)
    _remove(marklogic_api_client, TARGET_URI)
    _remove(marklogic_api_client, SOURCE_URI)


def test_merging_a_persisted_document_adds_a_version_and_removes_the_source(
    marklogic_api_client, merge_target, s3_calls
):
    # The source is created after the target so that it is the newer of the two.
    _insert_source(marklogic_api_client, SOURCE_URI)
    source = marklogic_api_client.get_document_by_uri(SOURCE_URI)
    source_body_xml = source.body.content_as_xml
    versions_before = _version_count(marklogic_api_client, TARGET_URI)

    merged = source.merge_into(TARGET_URI, "Merged in integration test", version_type=VersionType.SUBMISSION)

    assert merged.uri == TARGET_URI
    assert _version_count(marklogic_api_client, TARGET_URI) == versions_before + 1
    assert marklogic_api_client.get_document_by_uri(TARGET_URI).body.content_as_xml == source_body_xml
    assert not marklogic_api_client.document_exists(SOURCE_URI)
    assert [call[0] for call in s3_calls] == ["copy", "delete"]

    # The previous content is still held in MarkLogic's version history.
    version_uris = get_multipart_strings_from_marklogic_response(
        marklogic_api_client.list_judgment_versions(TARGET_URI)
    )
    first_version = DocumentURIString(
        min(version_uris, key=lambda uri: extract_version(uri) or 10**9).strip("/").removesuffix(".xml")
    )
    first_version_xml = marklogic_api_client.get_judgment_xml_bytestring(
        TARGET_URI, version_uri=first_version, show_unpublished=True
    )
    assert first_version_xml.decode() != source_body_xml
    assert "Content of the document being merged" not in first_version_xml.decode()

    assert marklogic_api_client.get_judgment_checkout_status_message(TARGET_URI) is None


def test_merging_an_in_memory_document_adds_a_version_and_touches_no_s3_assets(
    marklogic_api_client, merge_target, s3_calls
):
    source = document_from_xml(
        DocumentBody(_different_valid_judgment_xml().encode()), marklogic_api_client, uri=SOURCE_URI
    )
    versions_before = _version_count(marklogic_api_client, TARGET_URI)

    source.merge_into(TARGET_URI, "Merged in-memory document")

    assert _version_count(marklogic_api_client, TARGET_URI) == versions_before + 1
    assert not marklogic_api_client.document_exists(SOURCE_URI)
    assert s3_calls == []


def test_metadata_claims_survive_in_marklogic(marklogic_api_client, merge_target, s3_calls):
    # Identifiers are covered by unit tests: saving them needs the `compiled_url_slugs` SQL view, which the
    # harness database does not provide.
    existing_claim_ids = set(merge_target.metadata_fields)

    source = document_from_xml(
        DocumentBody(_different_valid_judgment_xml().encode()), marklogic_api_client, uri=SOURCE_URI
    )
    claim = MetadataField("title", MetadataStringValue("Title from the merged document"), MetadataSource.EDITOR)
    source.metadata_fields.add(claim)

    source.merge_into(TARGET_URI, "Merged with claims")

    stored = marklogic_api_client.get_document_by_uri(TARGET_URI)
    assert claim.id in stored.metadata_fields
    assert existing_claim_ids <= set(stored.metadata_fields)
    assert stored.metadata_fields[claim.id].value == claim.value
    assert stored.metadata_fields.resolve("title").value == claim.value


def test_failed_checks_leave_both_documents_untouched(marklogic_api_client, merge_target, s3_calls):
    _insert_source(marklogic_api_client, SOURCE_URI)
    source = marklogic_api_client.get_document_by_uri(SOURCE_URI)
    source.has_ever_been_published = True
    versions_before = _version_count(marklogic_api_client, TARGET_URI)

    with pytest.raises(DocumentMergeNotPossibleError):
        source.merge_into(TARGET_URI, "Should not happen")

    assert _version_count(marklogic_api_client, TARGET_URI) == versions_before
    assert marklogic_api_client.document_exists(SOURCE_URI)
    assert s3_calls == []
