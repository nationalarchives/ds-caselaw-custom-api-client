from unittest import TestCase
from unittest.mock import call, patch

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.documents import DocumentURIString


class TestGetPressSummariesForDocumentUri(TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    @patch("caselawclient.Client.PressSummary", autospec=True)
    @patch("caselawclient.Client.MarklogicApiClient._send_to_eval")
    @patch("caselawclient.Client.get_multipart_strings_from_marklogic_response")
    def test_get_press_summaries_for_document_uri(
        self,
        mock_get_marklogic_response,
        mock_eval,
        mock_press_summary,
    ):
        mock_eval.return_value = "EVAL"
        mock_get_marklogic_response.return_value = ["foo/bar/baz/1", "foo/bar/baz/2"]

        self.client.get_press_summaries_for_document_uri(DocumentURIString("foo/bar"))

        mock_get_marklogic_response.assert_called_with("EVAL")
        mock_eval.assert_called_with(
            {
                "parent_uri": "foo/bar",
                "component": "pressSummary",
            },
            "get_components_for_document.xqy",
        )

        mock_press_summary.assert_has_calls(
            [
                call("foo/bar/baz/1", self.client),
                call("foo/bar/baz/2", self.client),
            ],
            any_order=True,
        )
