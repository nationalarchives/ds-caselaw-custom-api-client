import os

import environ
from dotenv import load_dotenv

from caselawclient.Client import MarklogicApiClient

load_dotenv()
env = environ.Env()


def marklogic_configured() -> bool:
    host = os.environ.get("MARKLOGIC_HOST", "")
    user = os.environ.get("MARKLOGIC_USER", "")
    password = os.environ.get("MARKLOGIC_PASSWORD", "")
    return bool(host and user and password)


def build_marklogic_api_client() -> MarklogicApiClient:
    return MarklogicApiClient(
        host=env("MARKLOGIC_HOST"),
        username=env("MARKLOGIC_USER"),
        password=env("MARKLOGIC_PASSWORD"),
        use_https=env.bool("MARKLOGIC_USE_HTTPS", default=False),
    )
