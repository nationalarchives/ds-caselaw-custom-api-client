import json
from pathlib import Path
from uuid import uuid4

import pytest

from caselawclient.Client import ROOT_DIR
from caselawclient.errors import MarklogicAPIError, MarklogicMetricsStateChangedError
from caselawclient.factories import DocumentBodyFactory
from caselawclient.models.documents.metrics import DocumentMetrics
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.models.judgments import Judgment
from caselawclient.types import DocumentURIString

pytestmark = [pytest.mark.marklogic, pytest.mark.write]


@pytest.fixture
def metrics_document(marklogic_api_client, request):
    uri = DocumentURIString(f"test/metrics-{uuid4()}")
    body = DocumentBodyFactory.build()
    marklogic_api_client.insert_document_xml(
        uri,
        body.content_as_xml_tree,
        Judgment,
        VersionAnnotation(getattr(request, "param", VersionType.SUBMISSION), automated=True),
    )
    try:
        yield uri, body
    finally:
        marklogic_api_client.delete_judgment(uri)


def load_metrics(client, uri):
    return DocumentMetrics.from_etree(client.get_property_as_node(uri, "metrics"))


def submit(client, uri, body, version_type=VersionType.SUBMISSION):
    document = Judgment(uri, client)
    with document.editing_session():
        client.update_locked_document_xml(
            uri, body.content_as_xml_tree, VersionAnnotation(version_type, automated=True), validate_hash=False
        )


def test_submission_times_and_first_publication(marklogic_api_client, metrics_document):
    client = marklogic_api_client
    uri, body = metrics_document
    first = client.get_datetime_property(uri, "first_submission_datetime")
    assert first is not None
    assert client.get_datetime_property(uri, "latest_submission_datetime") == first

    submit(client, uri, body)
    latest = client.get_datetime_property(uri, "latest_submission_datetime")
    assert latest >= first
    assert client.get_datetime_property(uri, "first_submission_datetime") == first
    assert client.get_datetime_property(uri, "first_submission_after_latest_publication_datetime") is None

    for version_type in (VersionType.EDIT, VersionType.ENRICHMENT, VersionType.RESTORE):
        submit(client, uri, body, version_type)
    assert client.get_datetime_property(uri, "latest_submission_datetime") == latest

    # The legacy TDR timestamp must have no effect on reporting durations.
    client.set_property(uri, "transfer-received-at", "1900-01-01T00:00:00Z")
    client.publish_document(uri)
    published = client.get_datetime_property(uri, "first_published_datetime")
    metrics = load_metrics(client, uri)
    assert metrics.submissions_before_first_publish.value == 2
    assert metrics.tdr_to_first_publish.value == int((published - first).total_seconds())
    assert metrics.tdr_to_latest_publish.value == metrics.tdr_to_first_publish.value
    assert client.get_datetime_property(uri, "latest_published_datetime") == published
    assert client.get_published(uri)


def test_republication_freezes_first_metrics_and_clears_submission_date(marklogic_api_client, metrics_document):
    client = marklogic_api_client
    uri, body = metrics_document
    client.publish_document(uri)
    first_metrics = load_metrics(client, uri)
    first_published = client.get_datetime_property(uri, "first_published_datetime")
    client.set_published(uri, False)
    submit(client, uri, body)
    first_resubmission = client.get_datetime_property(uri, "first_submission_after_latest_publication_datetime")
    assert first_resubmission is not None
    submit(client, uri, body)
    assert client.get_datetime_property(uri, "first_submission_after_latest_publication_datetime") == first_resubmission

    client.publish_document(uri)
    metrics = load_metrics(client, uri)
    latest_published = client.get_datetime_property(uri, "latest_published_datetime")
    assert metrics.tdr_to_latest_publish.value == int((latest_published - first_resubmission).total_seconds())
    assert metrics.tdr_to_first_publish.value == first_metrics.tdr_to_first_publish.value
    assert metrics.submissions_before_first_publish.value == first_metrics.submissions_before_first_publish.value
    assert client.get_datetime_property(uri, "first_published_datetime") == first_published
    assert client.get_datetime_property(uri, "first_submission_after_latest_publication_datetime") is None

    client.publish_document(uri)
    assert load_metrics(client, uri).tdr_to_latest_publish.value is None
    assert load_metrics(client, uri).tdr_to_first_publish.value == first_metrics.tdr_to_first_publish.value

    # A new submission after publication starts a new measurement.
    submit(client, uri, body)
    assert client.get_datetime_property(uri, "first_submission_after_latest_publication_datetime") == (
        client.get_datetime_property(uri, "latest_submission_datetime")
    )


@pytest.mark.parametrize("metrics_document", [VersionType.EDIT], indirect=True)
def test_initial_edit_is_not_a_submission(marklogic_api_client, metrics_document):
    client = marklogic_api_client
    uri, body = metrics_document
    assert client.get_datetime_property(uri, "first_submission_datetime") is None
    assert client.get_datetime_property(uri, "latest_submission_datetime") is None
    submit(client, uri, body)
    assert client.get_datetime_property(uri, "first_submission_datetime") is not None
    client.publish_document(uri)
    assert load_metrics(client, uri).submissions_before_first_publish.value == 1


@pytest.mark.parametrize("publish", [False, True])
@pytest.mark.parametrize("change", ["properties", "history"])
def test_atomic_write_rejects_stale_state(marklogic_api_client, metrics_document, publish, change):
    client = marklogic_api_client
    uri, body = metrics_document
    with Judgment(uri, client).editing_session():
        state = client._get_document_metrics_state(uri)  # noqa: SLF001
        if change == "properties":
            client.set_published(uri, True)
        else:
            client.update_locked_document_xml(
                uri, body.content_as_xml_tree, VersionAnnotation(VersionType.EDIT, True), validate_hash=False
            )
        current = client._get_document_metrics_state(uri)  # noqa: SLF001
        assert current.signature != state.signature
        variables = {
            "uri": client._format_uri_for_marklogic(uri),  # noqa: SLF001
            "expected_state": state.signature,
            "properties": "<properties><published>false</published></properties>",
        }
        query = "publish_document.xqy"
        if not publish:
            query = "update_locked_judgment.xqy"
            annotation = VersionAnnotation(VersionType.SUBMISSION, True)
            annotation.set_calling_function("test_atomic_write_rejects_stale_state")
            annotation.set_calling_agent(client.user_agent)
            variables.update(
                judgment="<document>Rejected content</document>",
                annotation=annotation.as_json,
            )
        with pytest.raises(MarklogicMetricsStateChangedError):
            client.eval(str(Path(ROOT_DIR) / "xquery" / query), vars=json.dumps(variables))
        assert client._get_document_metrics_state(uri).signature == current.signature  # noqa: SLF001


@pytest.mark.parametrize("publish", [False, True])
@pytest.mark.parametrize("metrics_document", [VersionType.EDIT], indirect=True)
def test_property_failure_rolls_back_whole_write(marklogic_api_client, metrics_document, publish):
    client = marklogic_api_client
    uri, _ = metrics_document
    with Judgment(uri, client).editing_session():
        state = client._get_document_metrics_state(uri)  # noqa: SLF001
        original_xml = client.get_judgment_xml_bytestring(uri, show_unpublished=True)
        variables = {
            "uri": client._format_uri_for_marklogic(uri),  # noqa: SLF001
            "expected_state": state.signature,
            # DLS rejects writes to its own namespace. No preceding update may survive the error.
            "properties": (
                '<properties xmlns:dls="http://marklogic.com/xdmp/dls">'
                "<published>true</published><first_published_datetime>2026-01-02T00:00:00Z</first_published_datetime>"
                "<first_submission_datetime>2026-01-01T00:00:00Z</first_submission_datetime>"
                "<dls:invalid>invalid</dls:invalid></properties>"
            ),
        }
        query = "publish_document.xqy"
        if not publish:
            query = "update_locked_judgment.xqy"
            annotation = VersionAnnotation(VersionType.SUBMISSION, True)
            annotation.set_calling_function("test_property_failure_rolls_back_whole_write")
            annotation.set_calling_agent(client.user_agent)
            variables.update(
                judgment="<document>Rejected content</document>",
                annotation=annotation.as_json,
            )
        with pytest.raises(MarklogicAPIError) as error:
            client.eval(str(Path(ROOT_DIR) / "xquery" / query), vars=json.dumps(variables))
        assert not isinstance(error.value, MarklogicMetricsStateChangedError)
        assert client._get_document_metrics_state(uri).signature == state.signature  # noqa: SLF001
        assert client.get_judgment_xml_bytestring(uri, show_unpublished=True) == original_xml
