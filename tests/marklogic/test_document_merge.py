"""MarkLogic integration tests for Document.merge_into."""

import contextlib

import pytest

from caselawclient.Client import get_multipart_strings_from_marklogic_response
from caselawclient.client_helpers import document_from_xml
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
    MERGE_TEST_DOCUMENTS,
    TEST_MERGE_SOURCE_URI,
    TEST_MERGE_TARGET_URI,
    configure_merge_test_documents,
    reload_corpus_documents,
)

pytestmark = [pytest.mark.marklogic, pytest.mark.write]

TARGET_URI = TEST_MERGE_TARGET_URI
SOURCE_URI = TEST_MERGE_SOURCE_URI

MERGE_SOURCE_BODY_TEXT = "The applicant succeeded in their claim."


def _merge_source_fixture_xml() -> bytes:
    return (DOCUMENTS_DIR / "merge_source.xml").read_bytes()


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
        "caselawclient.models.documents.merge.copy_assets",
        lambda *args, **kwargs: calls.append(("copy", args, kwargs)),
    )
    monkeypatch.setattr(
        "caselawclient.models.documents.delete_documents_from_private_bucket", lambda uri: calls.append(("delete", uri))
    )
    return calls


@pytest.fixture
def merge_target(marklogic_api_client):
    """Reset the merge test corpus pair (target loaded before source)."""
    reload_corpus_documents(marklogic_api_client, MERGE_TEST_DOCUMENTS)
    configure_merge_test_documents(marklogic_api_client)
    yield marklogic_api_client.get_document_by_uri(TARGET_URI)
    _remove(marklogic_api_client, TARGET_URI)
    _remove(marklogic_api_client, SOURCE_URI)


def test_merging_a_persisted_document_adds_a_version_and_removes_the_source(
    marklogic_api_client, merge_target, s3_calls
):
    source = marklogic_api_client.get_document_by_uri(SOURCE_URI)
    source_body_xml = source.body.content_as_xml
    versions_before = _version_count(marklogic_api_client, TARGET_URI)

    merged = source.merge_into(TARGET_URI, "Merged in integration test", version_type=VersionType.SUBMISSION)

    assert merged.uri == TARGET_URI
    assert _version_count(marklogic_api_client, TARGET_URI) == versions_before + 1
    assert marklogic_api_client.get_document_by_uri(TARGET_URI).body.content_as_xml == source_body_xml
    assert not marklogic_api_client.document_exists(SOURCE_URI)
    assert [call[0] for call in s3_calls] == ["copy", "delete"]

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
    assert MERGE_SOURCE_BODY_TEXT not in first_version_xml.decode()

    assert marklogic_api_client.get_judgment_checkout_status_message(TARGET_URI) is None


def test_merging_an_in_memory_document_adds_a_version_and_touches_no_s3_assets(
    marklogic_api_client, merge_target, s3_calls
):
    _remove(marklogic_api_client, SOURCE_URI)
    source = document_from_xml(
        DocumentBody(_merge_source_fixture_xml()),
        marklogic_api_client,
        uri=SOURCE_URI,
    )
    versions_before = _version_count(marklogic_api_client, TARGET_URI)

    source.merge_into(TARGET_URI, "Merged in-memory document")

    assert _version_count(marklogic_api_client, TARGET_URI) == versions_before + 1
    assert not marklogic_api_client.document_exists(SOURCE_URI)
    assert s3_calls == []


def test_metadata_claims_survive_in_marklogic(marklogic_api_client, merge_target, s3_calls):
    # Structured identifiers on persisted merge fixtures are covered in test_merge_fixtures.py.
    existing_claim_ids = set(merge_target.metadata_fields)

    _remove(marklogic_api_client, SOURCE_URI)
    source = document_from_xml(
        DocumentBody(_merge_source_fixture_xml()),
        marklogic_api_client,
        uri=SOURCE_URI,
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
    marklogic_api_client.set_published(SOURCE_URI, True)
    source = marklogic_api_client.get_document_by_uri(SOURCE_URI)
    versions_before = _version_count(marklogic_api_client, TARGET_URI)

    with pytest.raises(DocumentMergeNotPossibleError):
        source.merge_into(TARGET_URI, "Should not happen")

    assert _version_count(marklogic_api_client, TARGET_URI) == versions_before
    assert marklogic_api_client.document_exists(SOURCE_URI)
    assert s3_calls == []
