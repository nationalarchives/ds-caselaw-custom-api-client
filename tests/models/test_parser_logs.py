from caselawclient.models.documents import DocumentURIString
from caselawclient.models.parser_logs import ParserLog


class TestParserLogValidation:
    def test_parser_log_has_type_collection_name(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = b"""
        <error>something went wrong</error>
        """

        parser_log = ParserLog(DocumentURIString("test/1234"), mock_api_client)
        parser_log.type_collection_name == "parser-log"
