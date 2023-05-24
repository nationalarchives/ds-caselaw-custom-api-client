import datetime

from lxml import etree

from caselawclient.search_result import SearchResult, SearchResultMeta


class TestSearchResult:
    def test_init(self):
        meta = SearchResultMeta()
        search_result = SearchResult(
            uri="test_uri",
            neutral_citation="test_neutral_citation",
            name="test_name",
            date=datetime.datetime(2022, 5, 22, 0, 0),
            court="test_court",
            matches="test_matches",
            content_hash="test_hash",
            transformation_date="test_transformation_date",
            meta=meta,
        )

        assert search_result.uri == "test_uri"
        assert search_result.neutral_citation == "test_neutral_citation"
        assert search_result.name == "test_name"
        assert search_result.date == datetime.datetime(2022, 5, 22, 0, 0)
        assert search_result.court == "test_court"
        assert search_result.matches == "test_matches"
        assert search_result.content_hash == "test_hash"
        assert search_result.transformation_date == "test_transformation_date"
        assert search_result.meta == meta

    def test_empty_init(self):
        search_result = SearchResult()

        assert search_result.uri == ""
        assert search_result.neutral_citation == ""
        assert search_result.name == ""
        assert search_result.court == ""
        assert search_result.date is None
        assert search_result.matches == ""
        assert search_result.content_hash == ""
        assert search_result.transformation_date == ""

    def test_create_from_node(self):
        xml = (
            '<search:result xmlns:search="http://marklogic.com/appservices/search" uri="/a/c/2015/20.xml" path="fn:doc(&quot;/a/c/2015/20.xml&quot;)">\n '  # noqa:E501
            "<search:snippet>"
            "<search:match path=\"fn:doc('/a/c/2015/20.xml')/*:akomaNtoso\">"
            "text from the document that matched the search"
            "</search:match>"
            "</search:snippet>"
            '<search:extracted kind="element">'
            '<FRBRdate date="2017-08-08" name="judgment" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
            '<FRBRname value="Another made up case name" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
            '<FRBRdate date="2023-04-09T18:05:45" name="transform" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'  # noqa:E501
            '<uk:court xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">A-C</uk:court>'
            '<uk:cite xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">[2015] A 20 (C)</uk:cite>'
            '<uk:hash xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">test_content_hash</uk:hash>'
            '<neutralCitation xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">[2015] A 0020 (C)</neutralCitation>'  # noqa:E501
            "</search:extracted>\n "
            "</search:result>\n "
        )
        node = etree.fromstring(xml)
        meta = SearchResultMeta()
        search_result = SearchResult.create_from_node(node, meta)

        assert search_result.uri == "a/c/2015/20"
        assert search_result.neutral_citation == "[2015] A 20 (C)"
        assert search_result.name == "Another made up case name"
        assert search_result.date == datetime.datetime(2017, 8, 8, 0, 0)
        assert search_result.court is None
        assert search_result.matches == (
            "<p data-path=\"fn:doc('/a/c/2015/20.xml')/*:akomaNtoso\">"
            "text from the document that matched the search</p>\n"
        )
        assert search_result.content_hash == "test_content_hash"
        assert search_result.transformation_date == "2023-04-09T18:05:45"
        assert search_result.meta == meta

    def test_create_from_node_with_unparsable_date(self):
        xml = (
            '<search:result xmlns:search="http://marklogic.com/appservices/search" uri="/a/c/2015/20.xml">\n '
            '<search:extracted kind="element">'
            '<FRBRdate date="blah" name="judgment" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
            "</search:extracted>\n "
            "</search:result>\n "
        )
        node = etree.fromstring(xml)
        meta = SearchResultMeta()
        search_result = SearchResult.create_from_node(node, meta)

        assert search_result.date is None

    def test_create_from_node_with_valid_court_code(self):
        xml = (
            '<search:result xmlns:search="http://marklogic.com/appservices/search" uri="/uksc/2015/20.xml">\n '  # noqa:E501
            '<search:extracted kind="element">'
            '<uk:court xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">UKSC</uk:court>'  # noqa:E501
            "</search:extracted>\n "
            "</search:result>\n "
        )
        node = etree.fromstring(xml)
        search_result = SearchResult.create_from_node(node, SearchResultMeta())

        assert search_result.court.name == "United Kingdom Supreme Court"

    def test_create_from_node_with_invalid_court_code(self):
        xml = (
            '<search:result xmlns:search="http://marklogic.com/appservices/search" index="2" uri="/a/c/2015/20.xml">\n '
            '<search:extracted kind="element">'
            '<uk:court xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">A-C</uk:court>'
            "</search:extracted>\n "
            "</search:result>\n "
        )
        node = etree.fromstring(xml)
        meta = SearchResultMeta()
        search_result = SearchResult.create_from_node(node, meta)

        assert search_result.date is None
