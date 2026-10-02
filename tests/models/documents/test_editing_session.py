"""Tests for Document.editing_session and editing lock requirements."""

import logging
import uuid

import pytest

from caselawclient.factories import JudgmentFactory
from caselawclient.models.documents.exceptions import (
    DocumentEditingSessionAlreadyActiveError,
    DocumentNotLockedForEditingError,
)
from caselawclient.models.documents.versions import VersionAnnotation, VersionType


@pytest.fixture(autouse=True)
def checkout_status_matches_session_token(mock_api_client):
    """MarkLogic reports the annotation of the most recent checkout as the current lock holder."""

    def _status(_uri: str) -> str | None:
        call = mock_api_client.checkout_judgment.call_args
        if call is None:
            return None
        return call.kwargs["annotation"]

    mock_api_client.get_judgment_checkout_status_message.side_effect = _status


@pytest.fixture
def unlocked_document(mock_api_client):
    return JudgmentFactory.build(api_client=mock_api_client, editing_lock_held=False)


def _session_token(mock_api_client) -> str:
    return mock_api_client.checkout_judgment.call_args.kwargs["annotation"]


class TestEditingSessionLifecycle:
    def test_checks_out_with_uuid_annotation(self, mock_api_client, unlocked_document):
        with unlocked_document.editing_session(timeout_seconds=30):
            token = _session_token(mock_api_client)
            assert uuid.UUID(token)
            assert unlocked_document.editing_session_token == token
            mock_api_client.checkout_judgment.assert_called_once_with(
                unlocked_document.uri,
                annotation=token,
                timeout_seconds=30,
            )

    def test_default_timeout_is_one_minute(self, mock_api_client, unlocked_document):
        with unlocked_document.editing_session():
            assert mock_api_client.checkout_judgment.call_args.kwargs["timeout_seconds"] == 60

    def test_clean_exit_checks_in_only_if_still_ours(self, mock_api_client, unlocked_document):
        with unlocked_document.editing_session():
            token = _session_token(mock_api_client)

        mock_api_client.checkin_judgment_if_ours.assert_called_once_with(unlocked_document.uri, token)
        mock_api_client.break_checkout_if_ours.assert_not_called()

    def test_error_exit_breaks_checkout_only_if_still_ours(self, mock_api_client, unlocked_document):
        with pytest.raises(ValueError, match="boom"), unlocked_document.editing_session():
            token = _session_token(mock_api_client)
            raise ValueError("boom")

        mock_api_client.break_checkout_if_ours.assert_called_once_with(unlocked_document.uri, token)
        mock_api_client.checkin_judgment_if_ours.assert_not_called()

    def test_keyboard_interrupt_breaks_checkout(self, mock_api_client, unlocked_document):
        with pytest.raises(KeyboardInterrupt), unlocked_document.editing_session():
            token = _session_token(mock_api_client)
            raise KeyboardInterrupt

        mock_api_client.break_checkout_if_ours.assert_called_once_with(unlocked_document.uri, token)

    def test_never_uses_unconditional_checkin_or_break(self, mock_api_client, unlocked_document):
        with unlocked_document.editing_session():
            pass
        with pytest.raises(ValueError, match="boom"), unlocked_document.editing_session():
            raise ValueError("boom")

        mock_api_client.checkin_judgment.assert_not_called()
        mock_api_client.break_checkout.assert_not_called()

    def test_failed_checkin_breaks_checkout_and_reraises(self, mock_api_client, unlocked_document):
        mock_api_client.checkin_judgment_if_ours.side_effect = RuntimeError("checkin failed")

        with pytest.raises(RuntimeError, match="checkin failed"), unlocked_document.editing_session():
            token = _session_token(mock_api_client)

        mock_api_client.break_checkout_if_ours.assert_called_once_with(unlocked_document.uri, token)
        assert unlocked_document.editing_session_token is None

    def test_failed_break_does_not_mask_original_error(self, mock_api_client, unlocked_document, caplog):
        mock_api_client.break_checkout_if_ours.side_effect = RuntimeError("break failed")

        with (
            caplog.at_level(logging.ERROR),
            pytest.raises(ValueError, match="boom"),
            unlocked_document.editing_session(),
        ):
            raise ValueError("boom")

        assert "Could not break checkout" in caplog.text

    def test_failed_checkout_releases_any_checkout_carrying_the_session_token(
        self,
        mock_api_client,
        unlocked_document,
    ):
        mock_api_client.checkout_judgment.side_effect = RuntimeError("checkout failed")

        with pytest.raises(RuntimeError, match="checkout failed"), unlocked_document.editing_session():
            pytest.fail("session body must not run when checkout fails")

        token = _session_token(mock_api_client)
        mock_api_client.break_checkout_if_ours.assert_called_once_with(unlocked_document.uri, token)
        mock_api_client.checkin_judgment_if_ours.assert_not_called()
        assert unlocked_document.editing_session_token is None

    def test_failed_release_after_failed_checkout_does_not_mask_checkout_error(
        self,
        mock_api_client,
        unlocked_document,
        caplog,
    ):
        mock_api_client.checkout_judgment.side_effect = RuntimeError("checkout failed")
        mock_api_client.break_checkout_if_ours.side_effect = RuntimeError("break failed")

        with (
            caplog.at_level(logging.ERROR),
            pytest.raises(RuntimeError, match="checkout failed"),
            unlocked_document.editing_session(),
        ):
            pass

        assert "Could not break checkout" in caplog.text
        assert unlocked_document.editing_session_token is None

    def test_local_lock_is_cleared_after_session(self, unlocked_document):
        with unlocked_document.editing_session():
            pass

        assert unlocked_document.editing_session_token is None
        with pytest.raises(DocumentNotLockedForEditingError):
            unlocked_document.hold()

    def test_nested_session_raises(self, unlocked_document):
        with (
            unlocked_document.editing_session(),
            pytest.raises(DocumentEditingSessionAlreadyActiveError),
            unlocked_document.editing_session(),
        ):
            pass

    def test_recovers_from_stale_local_lock(self, mock_api_client):
        document = JudgmentFactory.build(api_client=mock_api_client, editing_lock_held=True)
        document._editing_session_token = "stale-token"  # noqa: SLF001, S105

        with document.editing_session() as session:
            token = session.editing_session_token
            assert token is not None
            assert token != "stale-token"  # noqa: S105

        mock_api_client.checkin_judgment_if_ours.assert_called_once_with(document.uri, token)


class TestEditingLockRequirement:
    def test_save_update_without_lock_raises(self, mock_api_client, unlocked_document):
        with pytest.raises(DocumentNotLockedForEditingError):
            unlocked_document.save(message="Changed document")

        mock_api_client.update_locked_document_xml.assert_not_called()

    def test_save_update_inside_session_uses_update_locked_document_xml(self, mock_api_client, unlocked_document):
        with unlocked_document.editing_session():
            unlocked_document.save(message="Changed document")

        mock_api_client.update_locked_document_xml.assert_called_once()
        args = mock_api_client.update_locked_document_xml.call_args[0]
        assert args[0] == unlocked_document.uri
        assert isinstance(args[2], VersionAnnotation)
        assert args[2].version_type == VersionType.EDIT

    def test_save_raises_and_clears_local_lock_when_checkout_taken_by_another_session(
        self,
        mock_api_client,
        unlocked_document,
    ):
        with unlocked_document.editing_session():
            mock_api_client.get_judgment_checkout_status_message.side_effect = None
            mock_api_client.get_judgment_checkout_status_message.return_value = str(uuid.uuid4())

            with pytest.raises(DocumentNotLockedForEditingError, match="no longer locked"):
                unlocked_document.save(message="Changed document")

            assert unlocked_document.editing_session_token is None

        mock_api_client.update_locked_document_xml.assert_not_called()
