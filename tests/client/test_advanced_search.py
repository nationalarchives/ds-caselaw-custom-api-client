import json
import logging
import unittest
from unittest.mock import patch

import pytest

from caselawclient.Client import MarklogicApiClient
from caselawclient.search_parameters import SearchParameters


class TestAdvancedSearch(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "testuser", "", False)

    def test_invoke_called_with_default_params_when_optional_parameters_not_provided(
        self,
    ):
        """
        Scenario: Searching without specifying any arguments
        Given a client instance
        When the advanced_search method is called without any arguments
        Then it should call the MarkLogic module with the defaults
            parameters and return the response
        """

        with patch.object(self.client, "invoke"):
            response = self.client.advanced_search(SearchParameters())

            self.client.invoke.assert_called_with(
                "/judgments/search/search-v2.xqy",
                json.dumps(
                    {
                        "court": None,
                        "judge": "",
                        "page": 1,
                        "page-size": 10,
                        "q": "",
                        "party": "",
                        "neutral_citation": "",
                        "specific_keyword": "",
                        "order": "",
                        "from": "",
                        "to": "",
                        "show_unpublished": "false",
                        "only_unpublished": "false",
                        "collections": "",
                    }
                ),
            )

            assert response == self.client.invoke.return_value

    def test_invoke_called_with_all_params_when_all_parameters_provided(self):
        """
        Scenario: Searching with all parameters
        Given a client instance
        When the advanced_search method is called with all available parameters
        Then it should call the MarkLogic module with all the parameters
            and return the response
        """
        with patch.object(self.client, "invoke"):
            response = self.client.advanced_search(
                SearchParameters(
                    q="test query",
                    court="court",
                    judge="judge",
                    party="party",
                    neutral_citation="citation",
                    specific_keyword="keyword",
                    order="order",
                    date_from="2010-01-01",
                    date_to="2010-12-31",
                    page=2,
                    page_size=10,
                    show_unpublished=False,
                    only_unpublished=False,
                    collections=[" foo ", "abc def", " bar"],
                )
            )

            self.client.invoke.assert_called_with(
                "/judgments/search/search-v2.xqy",
                json.dumps(
                    {
                        "court": ["court"],
                        "judge": "judge",
                        "page": 2,
                        "page-size": 10,
                        "q": "test query",
                        "party": "party",
                        "neutral_citation": "citation",
                        "specific_keyword": "keyword",
                        "order": "order",
                        "from": "2010-01-01",
                        "to": "2010-12-31",
                        "show_unpublished": "false",
                        "only_unpublished": "false",
                        "collections": "foo,abcdef,bar",
                    }
                ),
            )

            assert response == self.client.invoke.return_value

    def test_exception_raised_when_invoke_raises_an_exception(self):
        """
        Scenario: MarkLogic exception while searching
        Given a client instance
        When the advanced_search method is called and MarkLogic returns an exception
        Then it should raise that same exception
        """
        exception = Exception("Error message from MarkLogic")
        with patch.object(self.client, "invoke"):
            self.client.invoke.side_effect = exception
            with pytest.raises(Exception) as e:
                self.client.advanced_search(SearchParameters(q="test query"))
        assert e.value == exception

    def test_user_can_view_unpublished_but_show_unpublished_is_false(
        self,
    ):
        """
        Scenario: User can view unpublished but show unpublished is false
        Given a client instance with a user who is allowed to view unpublished judgments
        When the advanced_search method is called with the show_unpublished parameter set to False
        Then it should call the MarkLogic module with the expected query parameters
        """
        with patch.object(self.client, "invoke") as mock_invoke:
            with patch.object(
                self.client, "user_can_view_unpublished_judgments", return_value=True
            ):
                self.client.advanced_search(
                    SearchParameters(
                        q="my-query",
                        court="ewhc",
                        judge="a. judge",
                        party="a party",
                        page=2,
                        page_size=20,
                        show_unpublished=False,
                    )
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
                    "collections": "",
                }

                mock_invoke.assert_called_with(
                    "/judgments/search/search-v2.xqy", json.dumps(expected_vars)
                )

    def test_user_can_view_unpublished_and_show_unpublished_is_true(
        self,
    ):
        """
        Scenario: User can view unpublished and show unpublished is true
        Given a client instance with a user who is allowed to view unpublished judgments
        When the advanced_search method is called with the show_unpublished parameter set to True
        Then it should call the MarkLogic module with the expected query parameters
        """
        with patch.object(self.client, "invoke"):
            with patch.object(
                self.client, "user_can_view_unpublished_judgments", return_value=True
            ):
                self.client.advanced_search(
                    SearchParameters(
                        q="my-query",
                        court="ewhc",
                        judge="a. judge",
                        party="a party",
                        page=2,
                        page_size=20,
                        show_unpublished=True,
                    )
                )
                assert (
                    '"show_unpublished": "true"' in self.client.invoke.call_args.args[1]
                )

    def test_user_cannot_view_unpublished_but_show_unpublished_is_true(
        self,
    ):
        """
        Scenario: User cannot view unpublished but show unpublished is true
        Given a client instance with a user who is not allowed to view unpublished judgments
        When the advanced_search method is called with the show_unpublished parameter set to True
        Then it should call the MarkLogic module with the show_unpublished parameter set to False and log a warning
        """
        with patch.object(self.client, "invoke"):
            with patch.object(
                self.client, "user_can_view_unpublished_judgments", return_value=False
            ):
                with patch.object(logging, "warning") as mock_logging:
                    self.client.advanced_search(
                        SearchParameters(
                            q="my-query",
                            court="ewhc",
                            judge="a. judge",
                            party="a party",
                            page=2,
                            page_size=20,
                            show_unpublished=True,
                        )
                    )

                    assert (
                        '"show_unpublished": "false"'
                        in self.client.invoke.call_args.args[1]
                    )
                    mock_logging.assert_called()

    def test_no_page_0(self):
        """
        Scenario: Requests for page 0 or lower are sent to page 1
        Given a client instance
        When the advanced_search method is called with the page parameter set to 0
        Then it should call the MarkLogic module with the page parameter set to 1
        """
        with patch.object(self.client, "invoke"):
            self.client.advanced_search(
                SearchParameters(
                    page=0,
                )
            )

            assert ', "page": 1,' in self.client.invoke.call_args.args[1]
