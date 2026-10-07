from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from lxml import etree

from caselawclient.factories import DocumentBodyFactory
from caselawclient.models.documents.metrics import DocumentMetrics
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.models.judgments import Judgment
from caselawclient.search_parameters import SearchParameters
from caselawclient.types import DocumentURIString

pytestmark = [pytest.mark.marklogic, pytest.mark.write]


@pytest.fixture
def reporting_documents(marklogic_api_client):
    client = marklogic_api_client
    keyword = f"reporting{uuid4().hex}"
    documents = []

    def create(value, published_at="2026-01-01T00:00:00Z", court="uksc", published=True):
        uri = DocumentURIString(f"test/reporting-{uuid4()}")
        body = DocumentBodyFactory.build(name=keyword, court=court)
        paragraph = body.content_as_xml_tree.find(".//{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}p")
        assert paragraph is not None
        paragraph.text = keyword
        client.insert_document_xml(uri, body.content_as_xml_tree, Judgment, VersionAnnotation(VersionType.EDIT, True))
        documents.append((uri, body))
        metrics = DocumentMetrics()
        for metric in metrics:
            metric.value = value
        client.set_property_as_node(uri, "metrics", metrics.as_etree)
        client.set_datetime_property(uri, "first_published_datetime", datetime.fromisoformat(published_at))
        client.set_datetime_property(uri, "latest_published_datetime", datetime(2026, 2, 1, tzinfo=UTC))
        client.set_published(uri, published)
        return uri, body

    try:
        yield keyword, create
    finally:
        for uri, _ in documents:
            client.delete_judgment(uri)


def report(client, keyword, metric="tdr_to_first_publish", bucketing="monthly", **filters):
    return client.get_metrics(
        metric=metric,
        bucketing=bucketing,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 1),
        search_parameters=SearchParameters(specific_keyword=keyword, **filters),
    )


def test_aggregates_weight_repeated_values_and_exclude_missing_metrics(marklogic_api_client, reporting_documents):
    client = marklogic_api_client
    keyword, create = reporting_documents
    for value in (0, 10, 10, 100, 200, None):
        create(value)
    create(999, published_at="2026-03-01T00:00:00Z")
    create(999, published_at="1970-01-01T00:00:00Z")
    monthly = report(client, keyword)
    assert monthly == {
        "2026-01": {"count": 5, "sum": 320, "mean": 64, "median": 10},
        "2026-02": {"count": 0, "sum": 0, "mean": None, "median": None},
    }
    daily = report(client, keyword, bucketing="daily")
    assert daily["2026-01-01"] == monthly["2026-01"]
    assert len(daily) == 59
    assert daily["2026-01-02"] == monthly["2026-02"]
    sentinel = client.get_metrics(
        metric="tdr_to_first_publish",
        bucketing="daily",
        start_date=date(1970, 1, 1),
        end_date=date(1970, 1, 2),
        search_parameters=SearchParameters(specific_keyword=keyword),
    )
    assert sentinel["1970-01-01"]["count"] == 0


@pytest.mark.parametrize(
    "metric", ["tdr_to_first_publish", "submissions_before_first_publish", "tdr_to_latest_publish"]
)
def test_metric_uses_its_publication_date(marklogic_api_client, reporting_documents, metric):
    keyword, create = reporting_documents
    create(3)
    create(4)
    result = report(marklogic_api_client, keyword, metric=metric)
    month = "2026-02" if metric == "tdr_to_latest_publish" else "2026-01"
    assert result[month] == {"count": 2, "sum": 7, "mean": 3.5, "median": 3.5}
    assert result["2026-01" if month == "2026-02" else "2026-02"]["count"] == 0


@pytest.mark.parametrize(
    ("filters", "count", "total"),
    [
        ({}, 3, 70),
        ({"court": "ewhc/qb"}, 2, 30),
        ({"court": "ewhc/qb,ukftt/credit"}, 3, 70),
        ({"collections": ["judgment"]}, 3, 70),
        ({"court": "ukftt/credit"}, 1, 40),
        ({"court": "uksc", "show_unpublished": True}, 1, 80),
        ({"only_unpublished": True}, 1, 80),
        ({"date_from": "2024-01-01"}, 0, 0),
    ],
)
def test_filters_match_search(marklogic_api_client, reporting_documents, filters, count, total):
    client = marklogic_api_client
    keyword, create = reporting_documents
    create(10, court="ewhc/qb")
    create(20, court="ewhc/kb")
    create(40, court="ukftt/credit")
    create(80, court="uksc", published=False)
    result = report(client, keyword, **filters)["2026-01"]
    assert result["count"] == count
    assert result["sum"] == total
    search = etree.fromstring(
        client.search_and_decode_response(SearchParameters(specific_keyword=keyword, page_size=100, **filters))
    )
    assert len(search.findall("{http://marklogic.com/appservices/search}result")) == count


def test_historical_versions_do_not_contribute(marklogic_api_client, reporting_documents):
    client = marklogic_api_client
    keyword, create = reporting_documents
    uri, body = create(100)
    with Judgment(uri, client).editing_session():
        client.update_locked_document_xml(
            uri, body.content_as_xml_tree, VersionAnnotation(VersionType.EDIT, True), validate_hash=False
        )
        metrics = DocumentMetrics()
        metrics.tdr_to_first_publish.value = 10
        client.set_property_as_node(uri, "metrics", metrics.as_etree)
    assert report(client, keyword)["2026-01"] == {"count": 1, "sum": 10, "mean": 10, "median": 10}
