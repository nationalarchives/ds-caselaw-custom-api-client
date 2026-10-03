"""MarkLogic integration tests for DLS checkout / editing_session behaviour."""

import contextlib
import uuid

import pytest

from caselawclient.Client import get_multipart_strings_from_marklogic_response
from caselawclient.errors import InvalidContentHashError, MarklogicAPIError, MarklogicResourceNotCheckedOutError
from caselawclient.models.documents.exceptions import DocumentNotLockedForEditingError
from marklogic_harness.corpus import TEST_PRESS_SUMMARY_URI

pytestmark = [pytest.mark.marklogic, pytest.mark.write]


def _release_document_checkout(client, uri) -> None:
    for action in (client.checkin_judgment, client.break_checkout):
        with contextlib.suppress(MarklogicAPIError):
            action(uri)


@pytest.fixture
def unlocked_metadata_writes_document(marklogic_api_client, metadata_writes_uri):
    _release_document_checkout(marklogic_api_client, metadata_writes_uri)
    document = marklogic_api_client.get_document_by_uri(metadata_writes_uri)
    yield document
    _release_document_checkout(marklogic_api_client, metadata_writes_uri)


def test_editing_session_stores_uuid_on_marklogic_checkout(unlocked_metadata_writes_document):
    document = unlocked_metadata_writes_document

    with document.editing_session(timeout_seconds=60) as session:
        token = session.editing_session_token
        assert token is not None
        uuid.UUID(token)
        assert document.api_client.get_judgment_checkout_status_message(document.uri) == token

    assert document.api_client.get_judgment_checkout_status_message(document.uri) is None


def test_second_checkout_by_same_user_replaces_lock_annotation(
    marklogic_api_client,
    unlocked_metadata_writes_document,
):
    document = unlocked_metadata_writes_document
    uri = document.uri
    first_annotation = str(uuid.uuid4())
    second_annotation = str(uuid.uuid4())

    marklogic_api_client.checkout_judgment(uri, annotation=first_annotation, timeout_seconds=60)
    try:
        marklogic_api_client.checkout_judgment(uri, annotation=second_annotation, timeout_seconds=60)
        assert marklogic_api_client.get_judgment_checkout_status_message(uri) == second_annotation
    finally:
        _release_document_checkout(marklogic_api_client, uri)


def test_second_editing_session_by_other_view_is_allowed(unlocked_metadata_writes_document):
    document = unlocked_metadata_writes_document
    other_view = document.api_client.get_document_by_uri(document.uri)

    with (
        document.editing_session(timeout_seconds=60) as first_session,
        other_view.editing_session(timeout_seconds=60) as second_session,
    ):
        assert first_session.editing_session_token is not None
        assert second_session.editing_session_token is not None
        assert second_session.editing_session_token != first_session.editing_session_token
        assert (
            document.api_client.get_judgment_checkout_status_message(document.uri)
            == second_session.editing_session_token
        )


def test_mutation_fails_after_checkout_broken_externally(unlocked_metadata_writes_document):
    document = unlocked_metadata_writes_document

    with (
        document.editing_session(timeout_seconds=60),
        pytest.raises(DocumentNotLockedForEditingError, match="no longer locked"),
    ):
        document.api_client.break_checkout(document.uri)
        document.hold()


def test_editing_session_breaks_checkout_on_keyboard_interrupt(unlocked_metadata_writes_document):
    document = unlocked_metadata_writes_document

    with pytest.raises(KeyboardInterrupt), document.editing_session(timeout_seconds=60):
        assert document.api_client.get_judgment_checkout_status_message(document.uri) is not None
        raise KeyboardInterrupt

    assert document.api_client.get_judgment_checkout_status_message(document.uri) is None


def test_editing_session_releases_checkout_committed_before_checkout_call_raised(
    unlocked_metadata_writes_document,
    monkeypatch,
):
    document = unlocked_metadata_writes_document
    client = document.api_client
    real_checkout = client.checkout_judgment

    def checkout_then_lose_response(*args, **kwargs):
        real_checkout(*args, **kwargs)
        raise TimeoutError("response lost after MarkLogic committed the checkout")

    monkeypatch.setattr(client, "checkout_judgment", checkout_then_lose_response)

    with pytest.raises(TimeoutError), document.editing_session(timeout_seconds=60):
        pytest.fail("session body must not run when checkout fails")

    assert client.get_judgment_checkout_status_message(document.uri) is None


@pytest.mark.parametrize("release", ["checkin_judgment_if_ours", "break_checkout_if_ours"])
def test_conditional_release_leaves_another_sessions_checkout_alone(
    marklogic_api_client,
    unlocked_metadata_writes_document,
    release,
):
    uri = unlocked_metadata_writes_document.uri
    other_session = str(uuid.uuid4())
    marklogic_api_client.checkout_judgment(uri, annotation=other_session, timeout_seconds=60)

    assert getattr(marklogic_api_client, release)(uri, str(uuid.uuid4())) is False
    assert marklogic_api_client.get_judgment_checkout_status_message(uri) == other_session


@pytest.mark.parametrize("release", ["checkin_judgment_if_ours", "break_checkout_if_ours"])
def test_conditional_release_releases_own_checkout(marklogic_api_client, unlocked_metadata_writes_document, release):
    uri = unlocked_metadata_writes_document.uri
    own_session = str(uuid.uuid4())
    marklogic_api_client.checkout_judgment(uri, annotation=own_session, timeout_seconds=60)

    assert getattr(marklogic_api_client, release)(uri, own_session) is True
    assert marklogic_api_client.get_judgment_checkout_status_message(uri) is None


@pytest.mark.parametrize("release", ["checkin_judgment_if_ours", "break_checkout_if_ours"])
def test_conditional_release_is_a_no_op_when_not_checked_out(
    marklogic_api_client,
    unlocked_metadata_writes_document,
    release,
):
    uri = unlocked_metadata_writes_document.uri

    assert getattr(marklogic_api_client, release)(uri, str(uuid.uuid4())) is False


def _version_count(client, uri) -> int:
    return len(get_multipart_strings_from_marklogic_response(client.list_judgment_versions(uri)))


def test_restore_document_inside_editing_session_keeps_the_session_checkout(unlocked_metadata_writes_document):
    document = unlocked_metadata_writes_document
    client = document.api_client
    versions_before = _version_count(client, document.uri)

    with document.editing_session(timeout_seconds=60) as session:
        client.restore_document(document.uri, versions_before)
        assert client.get_judgment_checkout_status_message(document.uri) == session.editing_session_token

    assert client.get_judgment_checkout_status_message(document.uri) is None
    assert _version_count(client, document.uri) == versions_before + 1


def test_restore_document_requires_a_checkout(marklogic_api_client, unlocked_metadata_writes_document):
    uri = unlocked_metadata_writes_document.uri
    with pytest.raises(MarklogicResourceNotCheckedOutError):
        marklogic_api_client.restore_document(uri, _version_count(marklogic_api_client, uri))


def test_save_inside_editing_session_writes_a_new_version_and_releases_checkout(unlocked_metadata_writes_document):
    document = unlocked_metadata_writes_document
    client = document.api_client
    versions_before = _version_count(client, document.uri)

    with document.editing_session(timeout_seconds=60):
        document.save(message="Saved inside editing session")

    assert client.get_judgment_checkout_status_message(document.uri) is None
    assert _version_count(client, document.uri) == versions_before + 1


def test_save_with_invalid_content_hash_fails_and_releases_checkout(unlocked_metadata_writes_document):
    document = unlocked_metadata_writes_document
    client = document.api_client
    versions_before = _version_count(client, document.uri)
    paragraph = document.body.content_as_xml_tree.xpath(
        "//akn:p",
        namespaces={"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"},
    )[0]
    paragraph.text = (paragraph.text or "") + " changed without updating the content hash"

    with pytest.raises(InvalidContentHashError), document.editing_session(timeout_seconds=60):
        document.save(message="Should be rejected")

    assert client.get_judgment_checkout_status_message(document.uri) is None
    assert _version_count(client, document.uri) == versions_before


def test_save_of_document_type_without_content_hash_succeeds(marklogic_api_client):
    uri = TEST_PRESS_SUMMARY_URI
    _release_document_checkout(marklogic_api_client, uri)
    document = marklogic_api_client.get_document_by_uri(uri)
    versions_before = _version_count(marklogic_api_client, uri)

    try:
        with document.editing_session(timeout_seconds=60):
            document.save(message="Saved press summary without a content hash")
    finally:
        _release_document_checkout(marklogic_api_client, uri)

    assert _version_count(marklogic_api_client, uri) == versions_before + 1
