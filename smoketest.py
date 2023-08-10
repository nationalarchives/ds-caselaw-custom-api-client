import environ
import pytest
from dotenv import load_dotenv

import caselawclient.Client as Client
from caselawclient.errors import DocumentNotFoundError

load_dotenv()
env = environ.Env()

URI = "smoketest/1001/1"

api_client = Client.MarklogicApiClient(
    host=env("MARKLOGIC_HOST"),
    username=env("MARKLOGIC_USER"),
    password=env("MARKLOGIC_PASSWORD"),
    use_https=env("MARKLOGIC_USE_HTTPS", default=None),
)


@pytest.mark.xfail
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
