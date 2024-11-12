import json
import os
import unittest
from unittest.mock import patch

from caselawclient.Client import ROOT_DIR, MarklogicApiClient, MarkLogicPrivilegeURIString


class TestUserPrivileges(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_user_has_privilege(self):
        with patch.object(self.client, "eval") as mock_eval:
            user = "laura"
            privilege_uri = MarkLogicPrivilegeURIString("https://caselaw.nationalarchives.gov.uk/custom/uri")
            privilege_action = "execute"
            expected_vars = {
                "user": "laura",
                "privilege_uri": "https://caselaw.nationalarchives.gov.uk/custom/uri",
                "privilege_action": "execute",
            }
            self.client.user_has_privilege(user, privilege_uri, privilege_action)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "user_has_privilege.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_user_can_view_unpublished_judgments_true(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"content-type: text/plain\r\n"
                b"X-Primitive: boolean\r\n\r\n"
                b"true\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.user_can_view_unpublished_judgments("laura")
            assert result is True

    def test_user_can_view_unpublished_judgments_false(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"content-type: text/plain\r\n"
                b"X-Primitive: boolean\r\n\r\n"
                b"false\r\n"
                b"--595658fa1db1aa98--\r\n"
            )

            result = self.client.user_can_view_unpublished_judgments("laura")
            assert result is False

    def test_user_can_view_unpublished_judgments_with_admin_role(self):
        with patch.object(self.client, "user_has_admin_role") as mock_user_has_admin:
            mock_user_has_admin.return_value = True
            result = self.client.user_can_view_unpublished_judgments("laura")
            assert result is True
