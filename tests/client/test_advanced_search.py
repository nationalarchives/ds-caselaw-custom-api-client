import json
import logging
import unittest
from unittest.mock import patch

from src.caselawclient.Client import MarklogicApiClient


class TestAdvancedSearch(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "testuser", "", False)

    def test_advanced_search_user_can_view_unpublished_but_show_unpublished_is_false(
        self,
    ):
        """If a user who is allowed to view unpublished judgments wishes to specifically see only published
        judgments, do not change the value of `show_unpublished`"""
        with patch.object(self.client, "invoke"):
            with patch.object(
                self.client, "user_can_view_unpublished_judgments", return_value=True
            ):
                self.client.advanced_search(
                    q="my-query",
                    court="ewhc",
                    judge="a. judge",
                    party="a party",
                    page=2,
                    page_size=20,
                    show_unpublished=False,
                )

                expected_vars = {
                    "court": ["ewhc"],
                    "judge": "a. judge",
                    "page": 2,
                    "page-size": 20,
                    "q": "my-query",
                    "party": "a party",
                    "neutral_citation": "",
                    "specific_keyword": "",
                    "order": "",
                    "from": "",
                    "to": "",
                    "show_unpublished": "false",
                    "only_unpublished": "false",
                }

                self.client.invoke.assert_called_with(
                    "/judgments/search/search-v2.xqy",
                    json.dumps(expected_vars),
                    transformation=None,
                )

    def test_advanced_search_user_can_view_unpublished_and_show_unpublished_is_true(
        self,
    ):
        """The user is permitted to see unpublished judgments and requests to see unpublished judgments"""
        with patch.object(self.client, "invoke"):
            with patch.object(
                self.client, "user_can_view_unpublished_judgments", return_value=True
            ):
                self.client.advanced_search(
                    q="my-query",
                    court="ewhc",
                    judge="a. judge",
                    party="a party",
                    page=2,
                    page_size=20,
                    show_unpublished=True,
                )
                assert (
                    '"show_unpublished": "true"' in self.client.invoke.call_args.args[1]
                )

    def test_advanced_search_user_cannot_view_unpublished_but_show_unpublished_is_true(
        self,
    ):
        """The user is not permitted to see unpublished judgments but is attempting to view them
        Set `show_unpublished` to false and log a warning"""
        with patch.object(self.client, "invoke"):
            with patch.object(
                self.client, "user_can_view_unpublished_judgments", return_value=False
            ):
                with patch.object(logging, "warning") as mock_logging:
                    self.client.advanced_search(
                        q="my-query",
                        court="ewhc",
                        judge="a. judge",
                        party="a party",
                        page=2,
                        page_size=20,
                        show_unpublished=True,
                    )

                    assert (
                        '"show_unpublished": "false"'
                        in self.client.invoke.call_args.args[1]
                    )
                    mock_logging.assert_called()

    def test_advanced_search_no_page_0(self):
        """Requests for page 0 or lower are sent to page 1."""
        with patch.object(self.client, "invoke"):
            self.client.advanced_search(
                page=0,
            )

            assert ', "page": 1,' in self.client.invoke.call_args.args[1]
