import logging
import unittest
from unittest.mock import patch

from src.caselawclient.Client import MarklogicApiClient


class TestVerifyShowUnpublished(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "testuser", "", False)

    # Test `verify_show_unpublished` with users who can/cannot see unpublished judgments
    # and with them asking for unpublished judgments or not
    def test_hide_published_if_unauthorised_and_user_asks_for_unpublished(self):
        # User cannot view unpublished but is asking to view unpublished judgments
        with patch.object(
            self.client,
            "user_can_view_unpublished_judgments",
            return_value=False,
        ):
            with patch.object(logging, "warning") as mock_logger:
                result = self.client.verify_show_unpublished(True)
                assert result is False
                # Check the logger was called
                mock_logger.assert_called()

    def test_show_unpublished_if_authorised_and_asks_for_unpublished(self):
        # User can view unpublished and is asking to view unpublished judgments
        with patch.object(
            self.client, "user_can_view_unpublished_judgments", return_value=True
        ):
            result = self.client.verify_show_unpublished(True)
            assert result is True

    def test_does_not_ask_for_unpublished(self):
        """
        User can view unpublished but is NOT asking to view unpublished judgments
        client.user_can_view_unpublished_judgments is not called because we check the value
        of show_unpublished first
        """
        with patch.object(
            self.client, "user_can_view_unpublished_judgments", return_value=True
        ):
            result = self.client.verify_show_unpublished(False)
            self.client.user_can_view_unpublished_judgments.assert_not_called()
            assert result is False
