import unittest
from unittest.mock import patch

from caselawclient.Client import MarklogicApiClient


class TestGetVersionAnnotation(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_get_version_annotation(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b"X-Primitive: text()\r\n"
                b"X-URI: /ewca/civ/2004/632.xml\r\n"
                b"X-Path: /prop:properties/published/text()\r\n"
                b"\r\nthis is an annotation\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_version_annotation("/judgment/uri")

            assert "this is an annotation" == result
