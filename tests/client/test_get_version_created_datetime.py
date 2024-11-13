import datetime
import unittest
from unittest.mock import patch

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.documents import DocumentURIString


class TestGetVersionCreatedDatetime(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_get_version_created_datetime(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b"X-Primitive: text()\r\n"
                b"X-URI: /ewca/civ/2004/632.xml\r\n"
                b"X-Path: /prop:properties/dls:version/dls:created/text()\r\n"
                b"\r\n2022-04-11T16:12:33.548954+01:00\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_version_created_datetime(DocumentURIString("judgment/uri"))

            assert result == datetime.datetime(
                2022,
                4,
                11,
                16,
                12,
                33,
                548954,
                datetime.timezone(datetime.timedelta(seconds=3600)),
            )
