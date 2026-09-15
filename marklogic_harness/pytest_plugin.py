import pytest

from caselawclient.Client import MarklogicApiClient
from marklogic_harness.client import build_marklogic_api_client, marklogic_configured


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "marklogic: integration test against a live MarkLogic database (requires MARKLOGIC_* env)",
    )


@pytest.fixture(scope="session")
def marklogic_api_client() -> MarklogicApiClient:
    if not marklogic_configured():
        pytest.skip("MARKLOGIC_HOST, MARKLOGIC_USER and MARKLOGIC_PASSWORD must be set")
    return build_marklogic_api_client()
