from lxml import etree

from caselawclient.Client import MarklogicApiClient
from caselawclient.responses.search_response import SearchResponse
from caselawclient.search_parameters import SearchParameters


def search_judgments_and_parse_response(
    api_client: MarklogicApiClient,
    search_parameters: SearchParameters,
) -> SearchResponse:
    """
    Search for judgments using the given search parameters and parse the response into a SearchResponse object.

    :param api_client: An instance of MarklogicApiClient used to make the search request
    :param search_parameters: An instance of SearchParameters containing the search parameters

    :return: The parsed search response as a SearchResponse object
    """
    return SearchResponse(
        etree.fromstring(
            api_client.search_judgments_and_decode_response(search_parameters),
        ),
        api_client,
    )


def search_and_parse_response(
    api_client: MarklogicApiClient,
    search_parameters: SearchParameters,
) -> SearchResponse:
    """
    Search using the given search parameters and parse the response into a SearchResponse object.

    :param api_client: An instance of MarklogicApiClient used to make the search request
    :search_parameters: An instance of SearchParameters containing the search parameters

    :return: The parsed search response as a SearchResponse object
    """
    return SearchResponse(
        etree.fromstring(api_client.search_and_decode_response(search_parameters)),
        api_client,
    )
