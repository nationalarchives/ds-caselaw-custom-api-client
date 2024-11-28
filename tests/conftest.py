from typing import Callable
from unittest.mock import Mock

import pytest

from caselawclient.Client import MarklogicApiClient


@pytest.fixture(name="valid_search_result_xml")
def valid_search_result_xml_fixture() -> str:
    """
    Fixture that provides a valid XML string representing a search result.

    Returns:
        str: Valid search result XML string.
    """
    return (
        '<search:result xmlns:search="http://marklogic.com/appservices/search" uri="/a/c/2015/20.xml" path="fn:doc(&quot;/a/c/2015/20.xml&quot;)">\n '
        "<search:snippet>"
        "<search:match path=\"fn:doc('/a/c/2015/20.xml')/*:akomaNtoso\">"
        "text from the document that matched the search"
        "</search:match>"
        "</search:snippet>"
        '<search:extracted kind="element">'
        '<FRBRdate date="2017-08-08" name="judgment" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
        '<FRBRname value="Another made up case name" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
        '<FRBRdate date="2023-04-09T18:05:45" name="transform" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
        '<uk:court xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">A-C</uk:court>'
        '<uk:cite xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">[2015] A 20 (C)</uk:cite>'
        '<uk:hash xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">test_content_hash</uk:hash>'
        '<neutralCitation xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">[2015] A 0020 (C)</neutralCitation>'
        "</search:extracted>"
        "</search:result>"
    )


@pytest.fixture(name="valid_facets_fixture_xml")
def valid_facets_xml_fixture() -> str:
    return (
        '<search:facet name="court" type="xs:string">'
        '<search:facet-value name="" count="14"/>'
        '<search:facet-value name=" UKUT-AAC" count="1"> UKUT-AAC</search:facet-value>'
        '<search:facet-value name="EAT" count="649">EAT</search:facet-value>'
        '<search:facet-value name="EWCA-Civil" count="5768">EWCA-Civil</search:facet-value>'
        "</search:facet>"
    )


@pytest.fixture(name="generate_search_response_xml")
def generate_search_response_xml_fixture() -> Callable:
    """
    Fixture that generates a valid search response XML string based on the provided content.

    Returns:
        Callable: Function that generates search response XML.
    """

    def _generate_search_response_xml(response_content: str, facets="") -> str:
        """
        Generate a search response XML string.

        Args:
            response_content (str): Content of the search response.

        Returns:
            str: Generated search response XML string.
        """
        return (
            '<search:response xmlns:search="http://marklogic.com/appservices/search" total="2">'
            f"{response_content}"
            f"{facets}"
            "</search:response>"
        )

    return _generate_search_response_xml


@pytest.fixture(name="valid_search_response_xml")
def valid_search_response_xml_fixture(
    generate_search_response_xml,
    valid_search_result_xml,
) -> str:
    """
    Fixture that provides a valid search response XML string.

    Args:
        generate_search_response_xml (Callable): Function to generate search response XML.
        valid_search_result_xml (str): Valid search result XML string.

    Returns:
        str: Valid search response XML string.
    """
    return generate_search_response_xml(valid_search_result_xml)


@pytest.fixture(name="generate_mock_search_response")
def generate_mock_response_fixture() -> Callable:
    """
    Fixture that generates a mock search response.

    Returns:
        Callable: Function that generates a mock search response.
    """

    def _generate_mock_response(search_response_xml: str) -> Mock:
        """
        Generate a mock search response.

        Args:
            search_response_xml (str): Search response XML.

        Returns:
            Mock: Generated mock search response.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "multipart/mixed; boundary=foo"}
        mock_response.content = (
            b"\r\n--foo\r\n"
            b"Content-Type: application/xml\r\n"
            b"X-Primitive: element()\r\nX-Path: /*:response\r\n\r\n" + search_response_xml.encode() + b"\r\n--foo--\r\n"
        )
        return mock_response

    return _generate_mock_response


@pytest.fixture
def mock_api_client():
    mock_client = Mock(spec=MarklogicApiClient)
    mock_client.get_judgment_xml_bytestring.return_value = b"<xml>content</xml>"
    mock_client.get_property_as_node.return_value = None

    return mock_client
