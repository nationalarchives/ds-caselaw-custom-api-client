import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from caselawclient.Client import MarklogicApiClient
from caselawclient.types import DocumentURIString

from ..test_helpers import MockMultipartResponse


class TestPendingParseReports(unittest.TestCase):
    """Check that our reporting functions for getting documents pending parsing are working as expected"""

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


class TestDocumentLockReports(unittest.TestCase):
    """Check that our reporting functions around document locking are working as expected"""

    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_get_locked_documents(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value = MockMultipartResponse("""
                <lock>
                    <document>/test/1234.xml</document>
                    <details>
                        <lock:lock
                            xmlns:lock="http://marklogic.com/xdmp/lock">
                            <lock:lock-type>write</lock:lock-type>
                            <lock:lock-scope>exclusive</lock:lock-scope>
                            <lock:active-locks>
                                <lock:active-lock>
                                    <lock:depth>0</lock:depth>
                                    <lock:owner>Judgment locked for editing by enrichment-engine</lock:owner>
                                    <lock:timeout>0</lock:timeout>
                                    <lock:lock-token>http://marklogic.com/xdmp/locks/a1b2c3d4</lock:lock-token>
                                    <lock:timestamp>1752871661</lock:timestamp>
                                    <sec:user-id
                                        xmlns:sec="http://marklogic.com/xdmp/security">1029384756
                                    </sec:user-id>
                                </lock:active-lock>
                            </lock:active-locks>
                        </lock:lock>
                    </details>
                </lock>
                """)

            result = self.client.get_locked_documents()

            assert len(result) == 1
            assert result[0].document_uri == DocumentURIString("test/1234")
            assert result[0].timestamp == datetime(2025, 7, 18, 20, 47, 41, tzinfo=UTC)
            assert result[0].timeout == 0
