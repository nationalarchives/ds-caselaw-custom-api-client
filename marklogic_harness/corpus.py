import json
from dataclasses import dataclass
from pathlib import Path

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.types import DocumentURIString

HARNESS_ROOT = Path(__file__).resolve().parent
DOCUMENTS_DIR = HARNESS_ROOT / "fixtures" / "documents"
INSERT_MANAGED_DOCUMENT_XQY = HARNESS_ROOT / "fixtures" / "insert_managed_document.xqy"

SMOKETEST_URI = DocumentURIString("smoketest/1001/2")

TEST_METADATA_WRITES_URI = DocumentURIString("test/metadata_writes")
TEST_MATCHING_SCHEMA_URI = DocumentURIString("test/matching_schema")
TEST_NOT_MATCHING_SCHEMA_URI = DocumentURIString("test/not_matching_schema")
TEST_PRESS_SUMMARY_PARENT_URI = DocumentURIString("test/press_summary_parent")
TEST_PRESS_SUMMARY_URI = DocumentURIString("test/press_summary")


@dataclass(frozen=True, slots=True)
class TestCorpusDocument:
    uri: DocumentURIString
    file_name: str
    type_collection: str
    version_annotation: str = ""


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
)


def load_test_corpus(client: MarklogicApiClient) -> None:
    for document in TEST_CORPUS_DOCUMENTS:
        _insert_managed_document(client, document)


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
