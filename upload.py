import glob

import environ
from dotenv import load_dotenv

from caselawclient import Client
from caselawclient.content_hash import get_hash_from_document
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.types import DocumentURIString

load_dotenv()
env = environ.Env()

Client.CONNECT_TIMEOUT = 99999.9
Client.READ_TIMEOUT = 99999.9

api_client = Client.MarklogicApiClient(
    host=env("MARKLOGIC_HOST"),
    username=env("MARKLOGIC_USER"),
    password=env("MARKLOGIC_PASSWORD"),
    use_https=env("MARKLOGIC_USE_HTTPS", default=None),
)

# these aren't obeyed ...

dryrun = False
for file in glob.glob("data/*"):
    print(file)

    with open(file, "rb") as f:
        content = f.read()
    print(get_hash_from_document(content))

    uri = DocumentURIString(file.partition("/")[2].replace("_", "/").strip(".xml"))
    print(f"{file} -> {uri}")

    annotation = VersionAnnotation(
        VersionType.EDIT, automated=False, message="Manual tweaks to ensure schema compliance", payload=dict()
    )
    if not dryrun:
        print("breaking")
        api_client.break_checkout(uri)
        print("locking")
        api_client.checkout_judgment(uri, "Lock for manual tweaks", timeout_seconds=60)
        print("saving")
        api_client.save_locked_judgment_xml(uri, content, annotation)
        print("done")
