import pytest

from marklogic_harness.corpus import SMOKETEST_URI, TEST_METADATA_WRITES_URI, load_test_corpus


@pytest.fixture(scope="session", autouse=True)
def _load_test_corpus(marklogic_api_client):
    load_test_corpus(marklogic_api_client)


@pytest.fixture
def smoketest_uri():
    return SMOKETEST_URI


@pytest.fixture
def metadata_writes_uri():
    return TEST_METADATA_WRITES_URI
