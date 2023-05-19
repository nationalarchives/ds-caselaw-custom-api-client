from unittest.mock import MagicMock

import pytest


@pytest.fixture(name="valid_search_response_xml")
def valid_search_response_xml_fixture() -> str:
    return (
        '<search:response xmlns:search="http://marklogic.com/appservices/search" total="2">'  # noqa: E501
        "<search:result>Result 1</search:result>"
        "<search:result>Result 2</search:result>"
        "</search:response>"
    )


@pytest.fixture(name="mock_search_results_response")
def mock_search_results_response_fixture(valid_search_response_xml) -> MagicMock:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "multipart/mixed; boundary=foo"}
    mock_response.content = (
        (
            b"\r\n--foo\r\n"
            b"Content-Type: application/xml\r\n"
            b"X-Primitive: element()\r\nX-Path: /*:response\r\n\r\n"
        )
        + valid_search_response_xml.encode()
        + b"\r\n--foo--\r\n"
    )
    return mock_response
