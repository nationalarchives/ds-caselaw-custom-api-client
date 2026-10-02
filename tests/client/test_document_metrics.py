from datetime import UTC, datetime
from unittest.mock import Mock, call, patch

import pytest
import time_machine
from lxml import etree

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.documents.metrics import DocumentMetrics
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.models.judgments import Judgment
from caselawclient.types import DocumentURIString

NOW = datetime(2026, 1, 2, tzinfo=UTC)
URI = DocumentURIString("test/metrics")
STATE = """<state>
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
        patch.object(client, "set_published"),
        patch.object(client, "set_datetime_property"),
        patch.object(client, "set_property_as_node"),
        patch.object(client, "set_property"),
    ):
        yield client


@time_machine.travel(NOW, tick=False)
def test_publish_uses_existing_property_methods(publishing_client):
    client = publishing_client
    response = client.publish_document(URI)
    assert response is client.set_published.return_value
    client.set_published.assert_called_once_with(URI, True)
    assert client.set_datetime_property.call_args_list == [
        call(URI, "first_published_datetime", NOW),
        call(URI, "latest_published_datetime", NOW),
    ]
    uri, name, node = client.set_property_as_node.call_args.args
    assert (uri, name) == (URI, "metrics")
    metrics = DocumentMetrics.from_etree(node)
    assert metrics.tdr_to_first_publish.value == 86400
    assert metrics.submissions_before_first_publish.value == 1
    client.set_property.assert_called_once_with(URI, "first_submission_after_latest_publication_datetime", "")


@time_machine.travel(NOW, tick=False)
def test_publish_does_not_write_existing_first_publication_date(publishing_client):
    client = publishing_client
    client._eval_and_decode.return_value = STATE.replace(  # noqa: SLF001
        "<properties>", "<properties><first_published_datetime>2025-01-01T00:00:00Z</first_published_datetime>"
    )
    client.publish_document(URI)
    client.set_datetime_property.assert_called_once_with(URI, "latest_published_datetime", NOW)


def test_failed_metrics_write_does_not_clear_first_submission_after_publication(publishing_client):
    client = publishing_client
    client.set_property_as_node.side_effect = RuntimeError("Property write failed")
    with pytest.raises(RuntimeError, match="Property write failed"):
        client.publish_document(URI)
    client.set_property.assert_not_called()
    client.set_published.assert_called_once_with(URI, True)


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
def test_submission_update_writes_timestamps_after_content(first_submission):
    client = MarklogicApiClient("", "", "", False)
    state = STATE
    if first_submission:
        state = state.replace(
            "<first_submission_datetime>2026-01-01T00:00:00Z</first_submission_datetime>", ""
        ).replace('"type":"submission"', '"type":"edit"')
    operations = Mock()
    with (
        patch.object(client, "_eval_and_decode", return_value=state) as read,
        patch.object(client, "_send_to_eval") as send,
        patch.object(client, "set_datetime_property") as write_property,
    ):
        operations.attach_mock(read, "read")
        operations.attach_mock(send, "save")
        operations.attach_mock(write_property, "write_property")
        response = client.update_document_xml(
            URI, etree.Element("document"), VersionAnnotation(VersionType.SUBMISSION, True)
        )
    read.assert_called_once_with({"uri": "/test/metrics.xml"}, "get_document_metrics_state.xqy")
    send.assert_called_once()
    assert response is send.return_value
    variables, query = send.call_args.args
    assert query == "update_document.xqy"
    assert set(variables) == {"uri", "judgment", "annotation"}
    expected_writes = [call(URI, "latest_submission_datetime", NOW)]
    if first_submission:
        expected_writes.insert(0, call(URI, "first_submission_datetime", NOW))
    assert write_property.call_args_list == expected_writes
    assert [operation[0] for operation in operations.mock_calls] == ["read", "save"] + ["write_property"] * len(
        expected_writes
    )


def test_failed_content_update_does_not_write_submission_timestamps():
    client = MarklogicApiClient("", "", "", False)
    with (
        patch.object(client, "_eval_and_decode", return_value=STATE),
        patch.object(client, "_send_to_eval", side_effect=RuntimeError("Content update failed")),
        patch.object(client, "set_datetime_property") as write_property,
        pytest.raises(RuntimeError, match="Content update failed"),
    ):
        client.update_document_xml(URI, etree.Element("document"), VersionAnnotation(VersionType.SUBMISSION, True))
    write_property.assert_not_called()


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
            client.update_document_xml(URI, etree.Element("document"), annotation)
    read.assert_not_called()
    write_property.assert_not_called()
    if insert:
        assert send.call_args.args[0]["properties"] == "<properties/>"
    else:
        assert set(send.call_args.args[0]) == {"uri", "judgment", "annotation"}
