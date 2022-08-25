import logging
import unittest
from unittest.mock import patch

from src.caselawclient.Client import MarklogicApiClient


class TestVerifyShowUnpublished(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    # Test `verify_show_unpublished` with users who can/cannot see unpublished judgments
    # and with them asking for unpublished judgments or not
    def test_hide_published_if_unauthorised_and_user_asks_for_unpublished(self):
        # User cannot view unpublished but is asking to view unpublished judgments
        with patch.object(
            self.client, "user_can_view_unpublished_judgments", return_value=False
        ):
            with patch.object(logging, "warning") as mock_logger:
                result = self.client.verify_show_unpublished(True)
                assert result is False
                # Check the logger was called
                mock_logger.assert_called()

    def test_hide_unpublished_if_unauthorised_and_does_not_ask_for_unpublished(self):
        # User cannot view unpublished and is not asking to view unpublished judgments
        with patch.object(
            self.client, "user_can_view_unpublished_judgments", return_value=False
        ):
            result = self.client.verify_show_unpublished(False)
            assert result is False

    def test_show_unpublished_if_authorised_and_asks_for_unpublished(self):
        # User can view unpublished and is asking to view unpublished judgments
        with patch.object(
            self.client, "user_can_view_unpublished_judgments", return_value=True
        ):
            result = self.client.verify_show_unpublished(True)
            assert result is True

    def test_hide_unpublished_if_authorised_and_does_not_ask_for_unpublished(self):
        # User can view unpublished but is NOT asking to view unpublished judgments
        with patch.object(
            self.client, "user_can_view_unpublished_judgments", return_value=True
        ):
            result = self.client.verify_show_unpublished(False)
            assert result is False
