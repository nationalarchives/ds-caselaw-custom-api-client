import datetime
from unittest.mock import patch

import pytest
from lxml import etree

from caselawclient.factories import DocumentBodyFactory, JudgmentFactory
from caselawclient.models.documents.exceptions import DocumentNotPersistedError
from caselawclient.models.documents.metrics import DocumentMetrics
from caselawclient.models.judgments import Judgment


def test_metrics_round_trip():
    metrics = DocumentMetrics()
    metrics.tdr_to_first_publish.value = 0
    metrics.tdr_to_latest_publish.value = 86461
    metrics.submissions_before_first_publish.value = 3
    loaded = DocumentMetrics.from_etree(metrics.as_etree)
    assert [(metric.key, metric.value) for metric in loaded] == [
        ("tdr_to_first_publish", 0),
        ("tdr_to_latest_publish", 86461),
        ("submissions_before_first_publish", 3),
    ]


@pytest.mark.parametrize("stored", [None, "<metrics/>"])
def test_historic_document_without_recorded_metrics(mock_api_client, stored):
    document = JudgmentFactory.build(api_client=mock_api_client)
    mock_api_client.get_property_as_node.return_value = etree.fromstring(stored) if stored else None
    assert all(metric.value is None for metric in document.metrics)
    assert len(document.metrics.as_etree) == 0
    mock_api_client.set_property_as_node.assert_not_called()


@pytest.mark.parametrize("value", [-1, 1.5, True, "12"])
def test_invalid_assignment(value):
    with pytest.raises(ValueError):
        DocumentMetrics().tdr_to_first_publish.value = value


@pytest.mark.parametrize(
    "xml",
    [
        "<wrong/>",
        "<metrics><unknown>1</unknown></metrics>",
        "<metrics><tdr_to_first_publish>1</tdr_to_first_publish><tdr_to_first_publish>2</tdr_to_first_publish></metrics>",
        "<metrics><tdr_to_first_publish>-1</tdr_to_first_publish></metrics>",
        "<metrics><tdr_to_first_publish>1.5</tdr_to_first_publish></metrics>",
        "<metrics><tdr_to_first_publish/></metrics>",
        "<metrics><tdr_to_first_publish><value>1</value></tdr_to_first_publish></metrics>",
    ],
)
def test_invalid_stored_metrics(xml):
    with pytest.raises(ValueError):
        DocumentMetrics.from_etree(etree.fromstring(xml))


def test_document_loads_and_explicitly_saves_metrics(mock_api_client):
    document = JudgmentFactory.build(api_client=mock_api_client)
    mock_api_client.get_property_as_node.return_value = etree.fromstring(
        "<metrics><tdr_to_first_publish>60</tdr_to_first_publish></metrics>"
    )
    assert document.metrics.tdr_to_first_publish.value == 60
    document.metrics.submissions_before_first_publish.value = 2
    document.save_metrics()
    uri, name, node = mock_api_client.set_property_as_node.call_args.args
    assert uri == document.uri
    assert name == "metrics"
    assert DocumentMetrics.from_etree(node).submissions_before_first_publish.value == 2


def test_new_document_has_empty_metrics(mock_api_client):
    mock_api_client.document_exists.return_value = False
    document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)
    assert document.metrics.tdr_to_first_publish.value is None
    with pytest.raises(DocumentNotPersistedError):
        document.save_metrics()


@pytest.mark.parametrize(
    "name",
    [
        "first_submission_datetime",
        "latest_submission_datetime",
        "first_submission_after_latest_publication_datetime",
    ],
)
def test_datetime_accessors_read_current_properties(mock_api_client, name):
    document = JudgmentFactory.build(api_client=mock_api_client)
    first = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    second = datetime.datetime(2026, 2, 1, tzinfo=datetime.UTC)
    mock_api_client.get_datetime_property.side_effect = [first, second]
    assert getattr(document, name) == first
    assert getattr(document, name) == second
    mock_api_client.get_datetime_property.assert_called_with(document.uri, name)


def test_content_save_does_not_overwrite_server_metrics(mock_api_client):
    document = JudgmentFactory.build(api_client=mock_api_client)
    document.metrics.tdr_to_first_publish.value = 100
    with (
        patch.object(document, "_save_structured_metadata_to_marklogic"),
        patch.object(document, "_save_identifiers_to_marklogic"),
    ):
        document.save("Edit")
    mock_api_client.set_property_as_node.assert_not_called()
