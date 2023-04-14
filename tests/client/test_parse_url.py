import pytest

from caselawclient.Client import MarklogicApiClient


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ["kitten", ["kitten"]],
        ["ewhc/qb", ["ewhc/qb", "ewhc/kb"]],
        ["ewhc/costs", ["ewhc/costs", "ewhc/scco"]],
        ["EWHC/KB,EWHC/scco", ["ewhc/qb", "ewhc/kb", "ewhc/costs", "ewhc/scco"]],
    ],
)
def test_court_list(test_input, expected):
    c = MarklogicApiClient("", "", "", "")._court_list
    assert set(c(test_input)) == set(expected)


def test_court_list_nothing():
    assert MarklogicApiClient("", "", "", "")._court_list("") is None
