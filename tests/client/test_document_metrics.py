from datetime import UTC, datetime
from unittest.mock import patch

import pytest
import time_machine
from lxml import etree

from caselawclient.Client import MarklogicApiClient
from caselawclient.errors import MarklogicMetricsStateChangedError
from caselawclient.models.documents.metrics import DocumentMetrics
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.models.judgments import Judgment
from caselawclient.types import DocumentURIString

NOW = datetime(2026, 1, 2, tzinfo=UTC)
URI = DocumentURIString("test/metrics")
STATE = """<state signature="initial-state">
  <properties>
    <first_submission_datetime>2026-01-01T00:00:00Z</first_submission_datetime>
  </properties>
  <dls:document-history xmlns:dls="http://marklogic.com/xdmp/dls">
    <dls:version>
      <dls:version-id>1</dls:version-id>
      <dls:annotation>{"type":"submission"}</dls:annotation>
    </dls:version>
  </dls:document-history>
</state>"""


@pytest.fixture
def publishing_client():
    client = MarklogicApiClient("", "", "", False)
    with (
        patch.object(client, "_eval_and_decode", return_value=STATE),
        patch.object(client, "_send_to_eval"),
        patch.object(client, "set_published"),
        patch.object(client, "set_datetime_property"),
        patch.object(client, "set_property_as_node"),
        patch.object(client, "set_property"),
    ):
        yield client


@time_machine.travel(NOW, tick=False)
def test_publish_writes_all_properties_in_one_request(publishing_client):
    client = publishing_client
    response = client.publish_document(URI)
    assert response is client._send_to_eval.return_value  # noqa: SLF001
    client._send_to_eval.assert_called_once()  # noqa: SLF001
    variables, query = client._send_to_eval.call_args.args  # noqa: SLF001
    assert query == "publish_document.xqy"
    assert variables["uri"] == "/test/metrics.xml"
    assert variables["expected_state"] == "initial-state"
    properties = etree.fromstring(variables["properties"])
    assert properties.findtext("published") == "true"
    assert properties.findtext("first_published_datetime") == NOW.isoformat()
    assert properties.findtext("latest_published_datetime") == NOW.isoformat()
    metrics = DocumentMetrics.from_etree(properties.find("metrics"))
    assert metrics.tdr_to_first_publish.value == 86400
    assert metrics.submissions_before_first_publish.value == 1
    assert properties.findtext("first_submission_after_latest_publication_datetime") == ""
    client.set_published.assert_not_called()
    client.set_datetime_property.assert_not_called()
    client.set_property_as_node.assert_not_called()
    client.set_property.assert_not_called()


@time_machine.travel(NOW, tick=False)
def test_publish_does_not_write_existing_first_publication_date(publishing_client):
    client = publishing_client
    client._eval_and_decode.return_value = STATE.replace(  # noqa: SLF001
        "<properties>", "<properties><first_published_datetime>2025-01-01T00:00:00Z</first_published_datetime>"
    )
    client.publish_document(URI)
    variables, _ = client._send_to_eval.call_args.args  # noqa: SLF001
    properties = etree.fromstring(variables["properties"])
    assert properties.find("first_published_datetime") is None
    assert properties.findtext("latest_published_datetime") == NOW.isoformat()


def test_failed_publication_is_not_retried(publishing_client):
    client = publishing_client
    client._send_to_eval.side_effect = RuntimeError("Property write failed")  # noqa: SLF001
    with pytest.raises(RuntimeError, match="Property write failed"):
        client.publish_document(URI)
    client._send_to_eval.assert_called_once()  # noqa: SLF001


def test_invalid_metrics_abort_before_database_write():
    client = MarklogicApiClient("", "", "", False)
    invalid = STATE.replace("<properties>", "<properties><metrics><unknown>1</unknown></metrics>")
    with (
        patch.object(client, "_eval_and_decode", return_value=invalid),
        patch.object(client, "_send_to_eval") as send,
        pytest.raises(ValueError, match="Unknown metric"),
    ):
        client.publish_document(URI)
    send.assert_not_called()


@time_machine.travel(NOW, tick=False)
@pytest.mark.parametrize("first_submission", [False, True])
def test_submission_update_writes_content_and_timestamps_in_one_request(first_submission):
    client = MarklogicApiClient("", "", "", False)
    state = STATE
    if first_submission:
        state = state.replace(
            "<first_submission_datetime>2026-01-01T00:00:00Z</first_submission_datetime>", ""
        ).replace('"type":"submission"', '"type":"edit"')
    with (
        patch.object(client, "_eval_and_decode", return_value=state) as read,
        patch.object(client, "_send_to_eval") as send,
        patch.object(client, "set_datetime_property") as write_property,
    ):
        response = client.update_locked_document_xml(
            URI, etree.Element("document"), VersionAnnotation(VersionType.SUBMISSION, True), validate_hash=False
        )
    read.assert_called_once_with({"uri": "/test/metrics.xml"}, "get_document_metrics_state.xqy")
    send.assert_called_once()
    assert response is send.return_value
    variables, query = send.call_args.args
    assert query == "update_locked_judgment.xqy"
    assert variables["expected_state"] == "initial-state"
    assert variables["judgment"] == "<document/>"
    properties = etree.fromstring(variables["properties"])
    assert properties.findtext("latest_submission_datetime") == NOW.isoformat()
    if first_submission:
        assert properties.findtext("first_submission_datetime") == NOW.isoformat()
    else:
        assert properties.find("first_submission_datetime") is None
    write_property.assert_not_called()


def test_failed_content_update_does_not_write_submission_timestamps():
    client = MarklogicApiClient("", "", "", False)
    with (
        patch.object(client, "_eval_and_decode", return_value=STATE),
        patch.object(client, "_send_to_eval", side_effect=RuntimeError("Content update failed")) as send,
        patch.object(client, "set_datetime_property") as write_property,
        pytest.raises(RuntimeError, match="Content update failed"),
    ):
        client.update_locked_document_xml(
            URI, etree.Element("document"), VersionAnnotation(VersionType.SUBMISSION, True), validate_hash=False
        )
    write_property.assert_not_called()
    send.assert_called_once()


@pytest.mark.parametrize("version_type", [VersionType.EDIT, VersionType.ENRICHMENT, VersionType.RESTORE])
@pytest.mark.parametrize("insert", [True, False])
def test_other_versions_do_not_read_or_change_metrics(version_type, insert):
    client = MarklogicApiClient("", "", "", False)
    with (
        patch.object(client, "_eval_and_decode") as read,
        patch.object(client, "_send_to_eval") as send,
        patch.object(client, "set_datetime_property") as write_property,
    ):
        annotation = VersionAnnotation(version_type, True)
        if insert:
            client.insert_document_xml(URI, etree.Element("document"), Judgment, annotation)
        else:
            client.update_locked_document_xml(URI, etree.Element("document"), annotation, validate_hash=False)
    read.assert_not_called()
    write_property.assert_not_called()
    if insert:
        assert send.call_args.args[0]["properties"] == "<properties/>"
    else:
        assert send.call_args.args[0]["properties"] == "<properties/>"
        assert send.call_args.args[0]["expected_state"] == ""


@pytest.mark.parametrize("publish", [False, True])
def test_state_conflict_is_not_retried(publish):
    client = MarklogicApiClient("", "", "", False)
    with (
        patch.object(client, "_eval_and_decode", return_value=STATE) as read,
        patch.object(client, "_send_to_eval", side_effect=MarklogicMetricsStateChangedError()) as send,
        pytest.raises(MarklogicMetricsStateChangedError),
    ):
        if publish:
            client.publish_document(URI)
        else:
            client.update_locked_document_xml(
                URI, etree.Element("document"), VersionAnnotation(VersionType.SUBMISSION, True), validate_hash=False
            )
    read.assert_called_once()
    send.assert_called_once()
