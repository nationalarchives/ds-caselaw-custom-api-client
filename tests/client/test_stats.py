import unittest
from unittest.mock import patch

from caselawclient.Client import MarklogicApiClient


class TestStats(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_get_combined_stats_table(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = '[["R1C1","R1C2"],["R2C1","R2C2"]]'
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
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
