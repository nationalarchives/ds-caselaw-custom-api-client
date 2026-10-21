"""End-to-end merge integration test for the merge_target / merge_source harness fixtures."""

import contextlib

import pytest

from caselawclient.errors import MarklogicAPIError
from caselawclient.models.documents.versions import VersionType
from caselawclient.models.identifiers.fclid import FindCaseLawIdentifier
from caselawclient.models.identifiers.neutral_citation import NeutralCitationNumber
from marklogic_harness.corpus import (
    MERGE_SOURCE_BODY,
    MERGE_SOURCE_NCN,
    MERGE_SOURCE_TITLE,
    MERGE_TARGET_BODY,
    MERGE_TARGET_NCN,
    MERGE_TARGET_TITLE,
    MERGE_TEST_ANNOTATION,
    MERGE_TEST_DOCUMENTS,
    TEST_MERGE_SOURCE_URI,
    TEST_MERGE_TARGET_URI,
    configure_merge_test_documents,
    configure_merge_test_identifiers,
    merge_test_expectations_for,
    reload_corpus_documents,
)

pytestmark = [pytest.mark.marklogic, pytest.mark.write]

TARGET_URI = TEST_MERGE_TARGET_URI
SOURCE_URI = TEST_MERGE_SOURCE_URI


def _remove(client, uri) -> None:
    if client.document_exists(uri):
        for action in (client.checkin_judgment, client.break_checkout):
            with contextlib.suppress(MarklogicAPIError):
                action(uri)
        client.delete_judgment(uri)


def _assert_metadata_properties_and_body(document, *, uri) -> None:
    expected = merge_test_expectations_for(uri)

    assert document.metadata_fields.resolve("title").value.value == expected.title
    assert expected.body_paragraph in document.body.content_as_xml
    assert document.neutral_citation == expected.neutral_citation

    for property_name, value in expected.properties.items():
        assert document.api_client.get_property(document.uri, property_name) == value


def _assert_identifiers(document, *, uri) -> None:
    expected = merge_test_expectations_for(uri)

    preferred_ncn = document.identifiers.preferred(type=NeutralCitationNumber)
    assert preferred_ncn is not None
    assert preferred_ncn.value == expected.neutral_citation
    assert preferred_ncn.deprecated is False
    assert document.identifiers.preferred(type=FindCaseLawIdentifier) is not None


def _ncn_values(document) -> dict[str, bool]:
    return {
        identifier.value: identifier.deprecated for identifier in document.identifiers.of_type(NeutralCitationNumber)
    }


@pytest.fixture
def s3_calls(monkeypatch):
    calls: list[tuple] = []
    monkeypatch.setattr(
        "caselawclient.models.documents.merge.copy_assets",
        lambda *args, **kwargs: calls.append(("copy", args, kwargs)),
    )
    monkeypatch.setattr(
        "caselawclient.models.documents.delete_documents_from_private_bucket",
        lambda uri: calls.append(("delete", uri)),
    )
    return calls


@pytest.fixture
def merge_test_pair(marklogic_api_client):
    reload_corpus_documents(marklogic_api_client, MERGE_TEST_DOCUMENTS)
    configure_merge_test_documents(marklogic_api_client)
    configure_merge_test_identifiers(marklogic_api_client)
    yield marklogic_api_client
    _remove(marklogic_api_client, TARGET_URI)
    _remove(marklogic_api_client, SOURCE_URI)


def test_merge_fixtures_merge_updates_xml_metadata_identifiers_and_properties(
    merge_test_pair,
    s3_calls,
):
    client = merge_test_pair
    target_before = client.get_document_by_uri(TARGET_URI)

    _assert_metadata_properties_and_body(target_before, uri=TARGET_URI)
    target_metadata_claim_ids = set(target_before.metadata_fields)
    target_identifier_values = {
        (identifier.schema.namespace, identifier.value) for identifier in target_before.identifiers.values()
    }

    source = client.get_document_by_uri(SOURCE_URI)
    source_metadata_claim_ids = set(source.metadata_fields)
    source_identifier_values = {
        (identifier.schema.namespace, identifier.value) for identifier in source.identifiers.values()
    }
    source_fclid = source.identifiers.preferred(type=FindCaseLawIdentifier)
    assert source_fclid is not None

    source.merge_into(TARGET_URI, MERGE_TEST_ANNOTATION, version_type=VersionType.SUBMISSION)

    assert not client.document_exists(SOURCE_URI)
    assert [call[0] for call in s3_calls] == ["copy", "delete"]

    merged = client.get_document_by_uri(TARGET_URI)
    merged_xml = merged.body.content_as_xml

    assert MERGE_SOURCE_BODY in merged_xml
    assert MERGE_TARGET_BODY not in merged_xml
    assert MERGE_SOURCE_TITLE in merged_xml
    assert MERGE_TARGET_TITLE not in merged_xml
    assert MERGE_SOURCE_NCN in merged_xml
    assert merged.neutral_citation == MERGE_SOURCE_NCN

    _assert_metadata_properties_and_body(merged, uri=SOURCE_URI)
    _assert_identifiers(merged, uri=SOURCE_URI)

    assert (target_metadata_claim_ids | source_metadata_claim_ids) <= set(merged.metadata_fields)
    merged_identifier_values = {
        (identifier.schema.namespace, identifier.value) for identifier in merged.identifiers.values()
    }
    assert (target_identifier_values | source_identifier_values) <= merged_identifier_values

    ncn_state = _ncn_values(merged)
    assert set(ncn_state) == {MERGE_SOURCE_NCN, MERGE_TARGET_NCN}
    assert ncn_state[MERGE_SOURCE_NCN] is False
    assert ncn_state[MERGE_TARGET_NCN] is True

    assert merged.identifiers.preferred(type=FindCaseLawIdentifier).value == source_fclid.value
