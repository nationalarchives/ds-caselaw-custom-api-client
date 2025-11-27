import unittest
from unittest.mock import patch

from caselawclient.Client import MarklogicApiClient


class TestReporting(unittest.TestCase):
    """Check that our reporting functions are continuing to make calls as expected"""

    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_get_highest_parser_version(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = '[["documents.process_data.parser_version_string", "documents.process_data.parser_major_version", "documents.process_data.parser_minor_version"], ["1.2.3", 1, 2]]'
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b'\r\n[["documents.process_data.parser_version_string", "documents.process_data.parser_major_version", "documents.process_data.parser_minor_version"], ["1.2.3", 1, 2]]\r\n'
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_highest_parser_version()

            assert result == (1, 2)

    def test_get_documents_pending_parse_for_version(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = '[["documents.process_data.uri", "documents.process_data.parser_version_string", "minutes_since_parse_request"], ["/ewhc/ch/2021/3432.xml", "0.3.1", 191015], ["/ewhc/ch/2019/3096.xml", "0.3.2", 191011], ["/ewhc/comm/2008/1186.xml", "0.3.2", 190951]]'
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b'\r\n[["documents.process_data.uri", "documents.process_data.parser_version_string", "minutes_since_parse_request"], ["/ewhc/ch/2021/3432.xml", "0.3.1", 191015], ["/ewhc/ch/2019/3096.xml", "0.3.2", 191011], ["/ewhc/comm/2008/1186.xml", "0.3.2", 190951]]\r\n'
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_documents_pending_parse_for_version(target_version=(1, 2))

            assert result == [
                [
                    "documents.process_data.uri",
                    "documents.process_data.parser_version_string",
                    "minutes_since_parse_request",
                ],
                ["/ewhc/ch/2021/3432.xml", "0.3.1", 191015],
                ["/ewhc/ch/2019/3096.xml", "0.3.2", 191011],
                ["/ewhc/comm/2008/1186.xml", "0.3.2", 190951],
            ]

    def test_get_count_pending_parse_for_version(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = '[["count"], [5678]]'
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b'\r\n[["count"], [5678]]\r\n'
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_count_pending_parse_for_version(target_version=(1, 2))

            assert result == 5678
