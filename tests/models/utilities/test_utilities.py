from unittest.mock import Mock

from src.caselawclient.models.utilities import (
    extract_version,
    get_judgment_root,
    render_versions,
)


class TestUtils:
    def test_get_judgment_root_error(self):
        xml = "<error>parser.log contents</error>"
        assert get_judgment_root(xml) == "error"

    def test_get_judgment_root_akomantoso(self):
        xml = (
            "<akomaNtoso xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn' "
            "xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0'>judgment</akomaNtoso>"
        )
        assert (
            get_judgment_root(xml)
            == "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}akomaNtoso"
        )

    def test_get_judgment_root_malformed_xml(self):
        # Should theoretically never happen but test anyway
        xml = "<error>malformed xml"
        assert get_judgment_root(xml) == "error"


class TestVersionUtils:
    def test_extract_version_uri(self):
        uri = "/ewhc/ch/2022/1178_xml_versions/2-1178.xml"
        assert extract_version(uri) == 2

    def test_extract_version_failure(self):
        uri = "/failures/TDR-2022-DBF_xml_versions/1-TDR-2022-DBF.xml"
        assert extract_version(uri) == 1

    def test_extract_version_not_found(self):
        uri = "some-other-string"
        assert extract_version(uri) == 0

    def test_render_versions(self):
        version_parts = (
            Mock(text="/ewhc/ch/2022/1178_xml_versions/3-1178.xml"),
            Mock(text="/ewhc/ch/2022/1178_xml_versions/2-1178.xml"),
            Mock(text="/ewhc/ch/2022/1178_xml_versions/1-1178.xml"),
        )
        requests_toolbelt = Mock()
        requests_toolbelt.multipart.decoder.BodyPart.return_value = version_parts

        expected_result = [
            {"uri": "/ewhc/ch/2022/1178_xml_versions/3-1178", "version": 3},
            {"uri": "/ewhc/ch/2022/1178_xml_versions/2-1178", "version": 2},
            {"uri": "/ewhc/ch/2022/1178_xml_versions/1-1178", "version": 1},
        ]

        assert render_versions(version_parts) == expected_result
