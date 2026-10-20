import json
import secrets
from dataclasses import dataclass
from pathlib import Path

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataStringValue
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.models.identifiers.fclid import FindCaseLawIdentifier, sqids
from caselawclient.models.identifiers.neutral_citation import NeutralCitationNumber
from caselawclient.types import DocumentURIString

HARNESS_ROOT = Path(__file__).resolve().parent
DOCUMENTS_DIR = HARNESS_ROOT / "fixtures" / "documents"
INSERT_MANAGED_DOCUMENT_XQY = HARNESS_ROOT / "fixtures" / "insert_managed_document.xqy"

SMOKETEST_URI = DocumentURIString("smoketest/1001/2")

TEST_METADATA_WRITES_URI = DocumentURIString("test/metadata_writes")
TEST_MERGE_TARGET_URI = DocumentURIString("test/merge_target")
TEST_MERGE_SOURCE_URI = DocumentURIString("test/merge_source")
TEST_MATCHING_SCHEMA_URI = DocumentURIString("test/matching_schema")
TEST_NOT_MATCHING_SCHEMA_URI = DocumentURIString("test/not_matching_schema")
TEST_PRESS_SUMMARY_PARENT_URI = DocumentURIString("test/press_summary_parent")
TEST_PRESS_SUMMARY_URI = DocumentURIString("test/press_summary")

MERGE_TEST_ANNOTATION = "Merged merge test corpus integration test"

MERGE_TARGET_BODY = "The applcant succeeded in their claim."
MERGE_SOURCE_BODY = "The applicant succeeded in their claim."

MERGE_TARGET_NCN = "[2023] EAT 100"
MERGE_SOURCE_NCN = "[2023] EAT 101"

MERGE_TARGET_TITLE = "Smith v Jnes"
MERGE_SOURCE_TITLE = "Smith v Jones"

MERGE_TARGET_PROPERTIES = {
    "source-name": "Wrong Submitter Name",
    "source-email": "wrong@example.com",
    "transfer-consignment-reference": "TDR-TARGET-001",
}

MERGE_SOURCE_PROPERTIES = {
    "source-name": "Correct Submitter Name",
    "source-email": "correct@example.com",
    "transfer-consignment-reference": "TDR-SOURCE-002",
}


@dataclass(frozen=True, slots=True)
class TestCorpusDocument:
    uri: DocumentURIString
    file_name: str
    type_collection: str
    version_annotation: str = ""


@dataclass(frozen=True, slots=True)
class MergeTestExpectations:
    title: str
    neutral_citation: str
    body_paragraph: str
    properties: dict[str, str]


def merge_test_expectations_for(uri: DocumentURIString) -> MergeTestExpectations:
    if uri == TEST_MERGE_TARGET_URI:
        return MergeTestExpectations(
            title=MERGE_TARGET_TITLE,
            neutral_citation=MERGE_TARGET_NCN,
            body_paragraph=MERGE_TARGET_BODY,
            properties=MERGE_TARGET_PROPERTIES,
        )
    if uri == TEST_MERGE_SOURCE_URI:
        return MergeTestExpectations(
            title=MERGE_SOURCE_TITLE,
            neutral_citation=MERGE_SOURCE_NCN,
            body_paragraph=MERGE_SOURCE_BODY,
            properties=MERGE_SOURCE_PROPERTIES,
        )
    raise ValueError(f"Not a merge test corpus URI: {uri}")


TEST_CORPUS_DOCUMENTS: tuple[TestCorpusDocument, ...] = (
    TestCorpusDocument(
        SMOKETEST_URI,
        "smoketest_judgment.xml",
        "judgment",
        "this is an annotation",
    ),
    TestCorpusDocument(
        TEST_METADATA_WRITES_URI,
        "metadata_writes.xml",
        "judgment",
        "metadata write fixture annotation",
    ),
    TestCorpusDocument(TEST_MATCHING_SCHEMA_URI, "matching_schema.xml", "judgment"),
    TestCorpusDocument(TEST_NOT_MATCHING_SCHEMA_URI, "not_matching_schema.xml", "judgment"),
    TestCorpusDocument(TEST_PRESS_SUMMARY_PARENT_URI, "press_summary_parent.xml", "judgment"),
    TestCorpusDocument(TEST_PRESS_SUMMARY_URI, "press_summary.xml", "press-summary"),
    TestCorpusDocument(
        TEST_MERGE_TARGET_URI,
        "merge_target.xml",
        "judgment",
        "merge demo target fixture",
    ),
    TestCorpusDocument(
        TEST_MERGE_SOURCE_URI,
        "merge_source.xml",
        "judgment",
        "merge demo source fixture",
    ),
)


def load_test_corpus(client: MarklogicApiClient) -> None:
    for document in TEST_CORPUS_DOCUMENTS:
        _insert_managed_document(client, document)


def reload_corpus_documents(client: MarklogicApiClient, documents: tuple[TestCorpusDocument, ...]) -> None:
    """Replace the given corpus documents (delete and insert from fixture XML)."""
    for document in documents:
        _insert_managed_document(client, document)


MERGE_TEST_DOCUMENTS: tuple[TestCorpusDocument, ...] = tuple(
    document for document in TEST_CORPUS_DOCUMENTS if document.uri in (TEST_MERGE_TARGET_URI, TEST_MERGE_SOURCE_URI)
)


def configure_merge_test_documents(client: MarklogicApiClient) -> None:
    """Apply structured metadata and ingest properties to persisted merge test fixtures."""
    for uri in (TEST_MERGE_TARGET_URI, TEST_MERGE_SOURCE_URI):
        _configure_merge_test_metadata_and_properties(client, uri)


def configure_merge_test_identifiers(client: MarklogicApiClient) -> None:
    """Persist structured identifiers on merge test fixtures (requires compiled_url_slugs TDE)."""
    for uri in (TEST_MERGE_TARGET_URI, TEST_MERGE_SOURCE_URI):
        _configure_merge_test_identifiers(client, uri)


def reload_merge_test_documents(client: MarklogicApiClient) -> None:
    """Reload merge test fixtures with metadata, properties, and identifiers."""
    reload_corpus_documents(client, MERGE_TEST_DOCUMENTS)
    configure_merge_test_documents(client)
    configure_merge_test_identifiers(client)


def _configure_merge_test_metadata_and_properties(client: MarklogicApiClient, uri: DocumentURIString) -> None:
    expected = merge_test_expectations_for(uri)
    client.set_published(uri, False)
    for property_name, value in expected.properties.items():
        client.set_property(uri, property_name, value)

    document = client.get_document_by_uri(uri)
    with document.editing_session():
        document.metadata_fields.add(
            MetadataField("title", MetadataStringValue(expected.title), MetadataSource.EDITOR),
        )
        document.save_metadata_fields()


def _configure_merge_test_identifiers(client: MarklogicApiClient, uri: DocumentURIString) -> None:
    expected = merge_test_expectations_for(uri)
    document = client.get_document_by_uri(uri)
    with document.editing_session():
        document.identifiers.add(NeutralCitationNumber(expected.neutral_citation))
        document.identifiers.add(FindCaseLawIdentifier(sqids.encode([secrets.randbits(63)])))
        document.save_identifiers()


def _insert_managed_document(client: MarklogicApiClient, document: TestCorpusDocument) -> None:
    if client.document_exists(document.uri):
        client.delete_judgment(document.uri)

    xml = (DOCUMENTS_DIR / document.file_name).read_text()
    variables = {
        "uri": document.uri.as_marklogic(),
        "document_xml": xml,
        "annotation": _version_annotation_json(client, document.version_annotation),
        "type_collection": document.type_collection,
    }
    client.eval(str(INSERT_MANAGED_DOCUMENT_XQY), vars=json.dumps(variables))


def _version_annotation_json(client: MarklogicApiClient, message: str) -> str:
    if not message:
        return ""
    annotation = VersionAnnotation(VersionType.SUBMISSION, automated=False, message=message)
    annotation.set_calling_function("load_test_corpus")
    annotation.set_calling_agent(client.user_agent)
    return annotation.as_json
