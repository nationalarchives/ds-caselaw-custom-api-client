import logging
from pathlib import Path

from caselawclient import Client
from marklogic_harness.client import build_marklogic_api_client

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSERTIONS_DIR = Path(__file__).resolve().parent
api_client = build_marklogic_api_client()

files = sorted(ASSERTIONS_DIR.glob("*.xqy"))
if not files:
    raise SystemExit(f"No assertion XQuery files found in {ASSERTIONS_DIR}")

for file in files:
    path = str(file)
    logger.info("Evaluating: %s", path)
    response = api_client.eval(path, vars="{}")
    logger.info("Response: %s", Client.get_multipart_strings_from_marklogic_response(response))
