import pytest

from caselawclient.search_parameters import SearchParameters


class TestSearchParametersToMarklogicData:
    def test_empty_init(self):
        """
        GIVEN an empty SearchParameters instance
        WHEN calling the as_marklogic_payload() method
        THEN it should return a dictionary with default values for all parameters
        """
        search_parameters = SearchParameters()
        assert search_parameters.as_marklogic_payload() == {
            "court": None,
            "judge": "",
            "page": 1,
            "page-size": 10,
            "q": "",
            "party": "",
            "neutral_citation": "",
            "name": "",
            "consignment_number": "",
            "specific_keyword": "",
            "order": "",
            "from": "",
            "to": "",
            "show_unpublished": "false",
            "only_unpublished": "false",
            "only_with_html_representation": "false",
            "collections": "",
            "quoted_phrases": [],
        }

    def test_specified_parameters(self):
        """
        GIVEN a SearchParameters instance with specified parameters
        WHEN calling the as_marklogic_payload() method
        THEN it should return a dictionary with the specified parameter values
        """
        search_parameters = SearchParameters(
            query="test query",
            court="test court",
            judge="test judge",
            party="test party",
            neutral_citation="test citation",
            name="test name",
            consignment_number="test consignment number",
            specific_keyword="test keyword",
            order=None,
            date_from="2022-01-01",
            date_to="2022-01-31",
            page=1,
            page_size=10,
            show_unpublished=False,
            only_unpublished=False,
            only_with_html_representation=False,
            collections=[" foo ", "abc def", " bar"],
        )
        assert search_parameters.as_marklogic_payload() == {
            "court": ["testcourt"],
            "judge": "test judge",
            "page": 1,
            "page-size": 10,
            "q": "test query",
            "party": "test party",
            "neutral_citation": "test citation",
            "name": "test name",
            "consignment_number": "test consignment number",
            "specific_keyword": "test keyword",
            "order": "",
            "from": "2022-01-01",
            "to": "2022-01-31",
            "show_unpublished": "false",
            "only_unpublished": "false",
            "only_with_html_representation": "false",
            "collections": "foo,abcdef,bar",
            "quoted_phrases": [],
        }

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ["kitten", ["kitten"]],
            ["ewhc/qb", ["ewhc/qb", "ewhc/kb"]],
            ["ewhc/costs", ["ewhc/costs", "ewhc/scco"]],
            ["EWHC/KB,EWHC/scco", ["ewhc/qb", "ewhc/kb", "ewhc/costs", "ewhc/scco"]],
        ],
    )
    def test_courts(self, test_input, expected):
        """
        GIVEN a SearchParameters instance with specified court parameter
        WHEN calling the as_marklogic_payload() method
        THEN the as_marklogic_payload() method should return a dictionary with the expected
            court values
        """
        search_parameters = SearchParameters(court=test_input)
        assert set(search_parameters.as_marklogic_payload()["court"]) == set(expected)

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ['"Reasonable adjustment" transport', ["Reasonable adjustment"]],
            ['"Reasonable adjustment"', ["Reasonable adjustment"]],
            ['transport "Reasonable adjustment"', ["Reasonable adjustment"]],
            [
                '"Reasonable adjustment" transport "Contractual obligation"',
                ["Reasonable adjustment", "Contractual obligation"],
            ],
        ],
    )
    def test_quoted_phrases(self, test_input, expected):
        """
        GIVEN a SearchParameters with a `query` containing a quoted phrase
        WHEN calling the as_marklogic_payload() method
        THEN the as_marklogic_payload() method should return a list of the quote phrases in the query.
        AND these phrases should remain in the query itself.
        """
        search_parameters = SearchParameters(query=test_input)
        payload = search_parameters.as_marklogic_payload()
        assert payload["quoted_phrases"] == expected
        assert payload["q"] == test_input
