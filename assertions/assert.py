import glob
import logging

import environ
from dotenv import load_dotenv

from caselawclient import Client

logger = logging.getLogger(__name__)

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
    logger.info("Evaluating: %s", path)
    response = api_client._send_to_eval({}, path)  ## noqa: SLF001
    logger.info("Response: %s", Client.get_multipart_strings_from_marklogic_response(response))
