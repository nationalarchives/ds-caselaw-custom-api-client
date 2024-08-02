import environ
import lxml
from dotenv import load_dotenv

import caselawclient.Client as Client

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

# print(Client.__file__)
# print(api_client.get_linked_caselaw("uksc/2024/1"))

namespaces = {
    "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "uk": "https://caselaw.nationalarchives.gov.uk/akn",
}

raw_bytes = Client.get_single_bytestring_from_marklogic_response(
    api_client.accessible_judgment_transformation("uksc/2024/1", show_unpublished=True)
)
root = lxml.html.fromstring(raw_bytes)
print(raw_bytes)
links = root.xpath("//ref[contains(@href, '')]", namespaces=namespaces)
for link in links:
    link.tail = ""
    print(lxml.html.tostring(link))

print(len(links))
