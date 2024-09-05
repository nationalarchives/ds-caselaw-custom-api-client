import environ
import pytest
from dotenv import load_dotenv

from caselawclient import Client
from caselawclient.errors import DocumentNotFoundError
from caselawclient.models.documents import Document

load_dotenv()
env = environ.Env()

URI = "smoketest/1001/2"
FIRST_VERSION_URI = "smoketest/1001/2_xml_versions/1-2"

api_client = Client.MarklogicApiClient(
    host=env("MARKLOGIC_HOST"),
    username=env("MARKLOGIC_USER"),
    password=env("MARKLOGIC_PASSWORD"),
    use_https=env("MARKLOGIC_USE_HTTPS", default=None),
)


def test_get_document_type_returns_404():
    with pytest.raises(DocumentNotFoundError) as e:
        api_client.get_document_type_from_uri("/not/a/real/url")
        assert e.status_code == 404


@pytest.mark.write
def test_set_metadata():
    api_client.set_document_court(URI, "EWHC-Chancellery")
    api_client.set_document_name(URI, "cats v dogs")
    api_client.set_document_work_expression_date(URI, "1001-02-03")
    doc = api_client.get_document_by_uri(URI)
    assert doc.court == "EWHC-Chancellery"
    assert doc.name == "cats v dogs"
    assert doc.document_date_as_string == "1001-02-03"


@pytest.mark.write
def test_get_version_annotation():
    assert api_client.get_version_annotation(FIRST_VERSION_URI) == "this is an annotation"
    assert Document(FIRST_VERSION_URI, api_client).annotation == "this is an annotation"


@pytest.mark.write
def test_get_highest_enrichment_version():
    value = api_client.get_highest_enrichment_version()
    assert int(value)


@pytest.mark.write
def test_get_press_summaries_for_document_uri():
    result = api_client.get_press_summaries_for_document_uri("/uksc/2023/35")
    assert len(result) == 1
    assert result[0].uri == "uksc/2023/35/press-summary/1"


@pytest.mark.write
@pytest.mark.parametrize(
    "document_uri,validates_against_schema",
    [("/ewca/civ/2004/632", False), ("/eat/2023/38", True)],
)
def test_invalid_document_is_invalid(document_uri, validates_against_schema):
    document = api_client.get_document_by_uri(document_uri)
    assert document.validates_against_schema is validates_against_schema
