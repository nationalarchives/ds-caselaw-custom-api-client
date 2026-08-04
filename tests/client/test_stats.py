import unittest
from pathlib import Path
from unittest.mock import patch

from caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestStats(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_get_combined_stats_table(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = '[["R1C1","R1C2"],["R2C1","R2C2"]]'
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b'\r\n[["R1C1","R1C2"],["R2C1","R2C2"]]\r\n'
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_combined_stats_table()

            assert result == [
                ["R1C1", "R1C2"],
                ["R2C1", "R2C2"],
            ]

    def test_get_courts_with_document_count(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = '{"uksc":12,"ukip":42}'
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b'\r\n{"uksc":12,"ukip":42}\r\n'
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_courts_with_document_count()

            assert result == {"uksc": 12, "ukip": 42}

    def test_get_courts_with_document_count_uses_court_metadata(self):
        xquery_path = Path(ROOT_DIR) / "xquery" / "get_courts_with_document_count.xqy"
        xquery = xquery_path.read_text(encoding="utf-8")

        assert 'declare namespace uk = "https://caselaw.nationalarchives.gov.uk/akn"' in xquery
        assert 'cts:element-values(xs:QName("uk:court")' in xquery
        assert "cts:uris" not in xquery

    def test_get_courts_with_document_count_normalises_hyphenated_compound_court_metadata(self):
        xquery_path = Path(ROOT_DIR) / "xquery" / "get_courts_with_document_count.xqy"

        assert 'fn:replace($court-param, "^(ewca|ewhc|ukut|ukftt|ftt)-", "$1/")' in xquery_path.read_text()
