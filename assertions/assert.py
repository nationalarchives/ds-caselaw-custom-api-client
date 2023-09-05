import glob

import environ
from dotenv import load_dotenv

import caselawclient.Client as Client

load_dotenv()
env = environ.Env()

api_client = Client.MarklogicApiClient(
    host=env("MARKLOGIC_HOST"),
    username=env("MARKLOGIC_USER"),
    password=env("MARKLOGIC_PASSWORD"),
    use_https=env("MARKLOGIC_USE_HTTPS", default=None),
)

files = glob.glob("*.xqy")

for file in files:
    path = f"../../../assertions/{file}"
    print(path)
    response = api_client._send_to_eval({}, path)
    print(Client.get_multipart_strings_from_marklogic_response(response))
