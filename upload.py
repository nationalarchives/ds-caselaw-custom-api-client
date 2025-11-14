import glob
from xml.etree import ElementTree as ET

import environ
from dotenv import load_dotenv

from caselawclient import Client
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.types import DocumentURIString
from caselawclient.content_hash import get_hash_from_document

load_dotenv()
env = environ.Env()

api_client = Client.MarklogicApiClient(
    host=env("MARKLOGIC_HOST"),
    username=env("MARKLOGIC_USER"),
    password=env("MARKLOGIC_PASSWORD"),
    use_https=env("MARKLOGIC_USE_HTTPS", default=None),
)

ET.register_namespace("", "http://docs.oasis-open.org/legaldocml/ns/akn/3.0")
ET.register_namespace("html", "http://www.w3.org/1999/xhtml")
ET.register_namespace("uk", "https://caselaw.nationalarchives.gov.uk/akn")

dryrun = False
for file in glob.glob("data/*"):
    print(file)
    xml_element = ET.parse(file).getroot()

    with open(file, 'rb') as f:
        content = f.read()
    # xml_element = ET.fromstring(content)
    print(get_hash_from_document(content))

    uri = DocumentURIString(file.partition("/")[2].replace("_", "/").strip(".xml"))
    print(f"{file} -> {uri} {xml_element}")
    
    annotation = VersionAnnotation(
        VersionType.EDIT, automated=False, message="Manual tweaks to ensure schema compliance", payload=dict()
    )
    if not dryrun:
        api_client.update_document_xml(uri, xml_element, annotation=annotation)
