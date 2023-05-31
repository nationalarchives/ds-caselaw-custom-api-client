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
            "specific_keyword": "",
            "order": "",
            "from": "",
            "to": "",
            "show_unpublished": "false",
            "only_unpublished": "false",
            "collections": "",
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
            specific_keyword="test keyword",
            order=None,
            date_from="2022-01-01",
            date_to="2022-01-31",
            page=1,
            page_size=10,
            show_unpublished=False,
            only_unpublished=False,
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
            "specific_keyword": "test keyword",
            "order": "",
            "from": "2022-01-01",
            "to": "2022-01-31",
            "show_unpublished": "false",
            "only_unpublished": "false",
            "collections": "foo,abcdef,bar",
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
