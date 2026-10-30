from unittest.mock import patch

import pytest
from lxml import etree

from caselawclient.Client import MarklogicApiClient
from caselawclient.responses.search_response import SearchResponse
from caselawclient.responses.search_result import SearchResult


class TestSearchResponse:
    @pytest.fixture(autouse=True)
    def mock_properties(self):
        with patch.object(
            MarklogicApiClient, "get_properties_for_search_results", return_value="<property-results/>"
        ) as mock:
            yield mock

    def setup_method(self):
        self.client = MarklogicApiClient(
            host="",
            username="",
            password="",
            use_https=False,
            user_agent="marklogic-api-client-test",
        )

    def test_multi_identifier(self):
        """
        Ensure that if multiple search results exist, each gets the identifier for that result.
        There was a bug where it would get the first result from anywhere in the document.
        Some odd behaviour -- it determines the slug from the value, not the url_slug;
        this is fine, because it's calculated the same way, but is counterintuitive.
        """
        search_response = SearchResponse(
            etree.fromstring(
                """
                <search:response xmlns:search="http://marklogic.com/appservices/search" total="5">
                <search:result xmlns:search="http://marklogic.com/appservices/search" uri="/uksc/2015/20.xml">
                <search:extracted kind="identifiers">
                <identifiers>
                    <identifier>
                        <namespace>ukncn</namespace>
                        <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                        <value>[1901] UKSC 1</value>
                        <url_slug>uksc/1901/1</url_slug>
                    </identifier>
                </identifiers>
                </search:extracted>
                </search:result>
                <search:result xmlns:search="http://marklogic.com/appservices/search" uri="/uksc/2015/20.xml">
                <search:extracted kind="identifiers">
                <identifiers>
                    <identifier>
                        <namespace>ukncn</namespace>
                        <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                        <value>[1901] UKSC 4444</value>
                        <url_slug>uksc/1901/4444</url_slug>
                    </identifier>
                </identifiers>
                </search:extracted>
                </search:result>
                "</search:response>"""
            ),
            self.client,
        )
        assert search_response.results[0].slug == "uksc/1901/1"
        assert search_response.results[1].slug == "uksc/1901/4444"

    def test_total(
        self,
    ):
        """
        Given a SearchResponse instance
        When calling 'total' on it
        Then it should return an integer representing the total number of results
        """
        search_response = SearchResponse(
            etree.fromstring(
                '<search:response xmlns:search="http://marklogic.com/appservices/search" total="5">'
                "foo"
                "</search:response>",
            ),
            self.client,
        )

        assert search_response.total == 5

    def test_result_metadata_is_loaded_once_for_the_page(
        self, valid_search_result_xml, generate_search_response_xml, mock_properties
    ):
        root = etree.fromstring(generate_search_response_xml(2 * valid_search_result_xml))
        nodes = root.findall("{http://marklogic.com/appservices/search}result")
        nodes[0].set("uri", "/test/first.xml")
        nodes[1].set("uri", "/test/second.xml")
        mock_properties.return_value = """
        <property-results>
          <property-result uri="/test/second.xml" last-modified="2026-02-02T00:00:00Z">
            <source-name>Second author</source-name>
            <metadata_fields>
              <metadata id="9b2c8e4f-1a3d-4c5e-8f7a-6b0d9e2c1a34" name="title" source="editor"
                timestamp="2026-01-01T00:00:00Z">Second title</metadata>
            </metadata_fields>
          </property-result>
          <property-result uri="/test/first.xml" last-modified="2026-02-01T00:00:00Z">
            <source-name>First author</source-name>
            <metadata_fields>
              <metadata id="2d80bf1d-e3ea-452f-965c-041f4399f2dd" name="title" source="editor"
                timestamp="2026-01-01T00:00:00Z">First title</metadata>
            </metadata_fields>
          </property-result>
        </property-results>
        """
        response = SearchResponse(root, self.client)
        with patch.object(self.client, "get_last_modified") as get_last_modified:
            assert [result.name for result in response.results] == ["First title", "Second title"]
            assert [result.metadata.author for result in response.results] == ["First author", "Second author"]
            assert [result.metadata.last_modified for result in response.results] == [
                "2026-02-01T00:00:00Z",
                "2026-02-02T00:00:00Z",
            ]
            assert response.results is response.results
            mock_properties.assert_called_once_with(["test/first", "test/second"])
            get_last_modified.assert_not_called()

    def test_empty_results_do_not_load_properties(self, mock_properties):
        response = SearchResponse(
            etree.fromstring('<search:response xmlns:search="http://marklogic.com/appservices/search" total="0"/>'),
            self.client,
        )
        assert response.results == []
        mock_properties.assert_not_called()

    @pytest.mark.parametrize("batched", [True, False])
    @pytest.mark.parametrize("external", [True, False])
    def test_properties_do_not_expand_entities(self, mock_properties, tmp_path, batched, external):
        secret = tmp_path / "secret.txt"
        secret.write_text("private content")
        entity = f'SYSTEM "{secret.as_uri()}"' if external else '"expanded content"'
        mock_properties.return_value = (
            f"<!DOCTYPE property-results [<!ENTITY unsafe {entity}>]>"
            '<property-results><property-result uri="/test/example.xml">'
            "<source-name>&unsafe;</source-name>"
            "</property-result></property-results>"
        )
        root = etree.fromstring(
            '<search:response xmlns:search="http://marklogic.com/appservices/search">'
            '<search:result uri="/test/example.xml"/></search:response>'
        )
        result = SearchResponse(root, self.client).results[0] if batched else SearchResult(root[0], self.client)
        assert result.metadata.author == ""
        assert result.metadata.node.xpath(".//source-name/text()") == []

    def test_results(
        self,
        valid_search_result_xml,
        generate_search_response_xml,
    ):
        """
        Given a SearchResponse instance with n results
        When calling 'results' on it
        Then it should return a list of n SearchResult elements
        And each element's node attribute should be as expected
        """
        search_response = SearchResponse(
            etree.fromstring(generate_search_response_xml(2 * valid_search_result_xml)),
            self.client,
        )

        results = search_response.results

        assert len(results) == 2
        assert etree.tostring(results[0].node) == etree.tostring(
            etree.fromstring(valid_search_result_xml),
        )
        assert etree.tostring(results[1].node) == etree.tostring(
            etree.fromstring(valid_search_result_xml),
        )

    def test_when_search_namespace_prefix_not_defined_on_response_xml_syntax_error_raised(
        self,
    ):
        """
        Given an XML response without the 'search' namespace prefix defined
        When creating SearchResponse instance with the XML
        Then a XMLSyntaxError with the expected message should be raised
        """
        xml_without_namespace = (
            '<search:response xmlns:foo="http://marklogic.com/appservices/search" total="2">'
            "<search:result>Result 1</search:result>"
            "<search:result>Result 2</search:result>"
            "</search:response>"
        )
        with pytest.raises(
            etree.XMLSyntaxError,
            match="Namespace prefix search on response is not defined",
        ):
            SearchResponse(etree.fromstring(xml_without_namespace), self.client)

    def test_facets(
        self,
        valid_search_result_xml,
        valid_facets_fixture_xml,
        generate_search_response_xml,
    ):
        """
        Given a SearchResponse instance with n facets
        When calling 'facets' on it
        Then it should return a list of n elements
        And each element's node attribute should be as expected
        """
        search_response = SearchResponse(
            etree.fromstring(
                generate_search_response_xml(
                    valid_search_result_xml,
                    valid_facets_fixture_xml,
                ),
            ),
            self.client,
        )

        results = search_response.facets

        assert len(results) == 4
        assert results[""] == "14"
        assert results[" UKUT-AAC"] == "1"
        assert results["EAT"] == "649"
        assert results["EWCA-Civil"] == "5768"
