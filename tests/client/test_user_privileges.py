import json
import os
import unittest
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestUserPrivileges(unittest.TestCase):
    def test_user_has_privilege(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            user = "laura"
            privilege_uri = "https://caselaw.nationalarchives.gov.uk/custom/uri"
            privilege_action = "execute"
            expected_vars = {
                "user": "laura",
                "privilege_uri": "https://caselaw.nationalarchives.gov.uk/custom/uri",
                "privilege_action": "execute",
            }
            client.user_has_privilege(user, privilege_uri, privilege_action)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "user_has_privilege.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_user_can_view_unpublished_judgments_true(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = "true"

            result = client.user_can_view_unpublished_judgments("laura")
            assert result is True

    def test_user_can_view_unpublished_judgments_false(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = "false"

            result = client.user_can_view_unpublished_judgments("laura")
            assert result is False
