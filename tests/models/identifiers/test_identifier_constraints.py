from unittest.mock import patch

import pytest
from test_identifiers import TestIdentifier, TestIdentifierSchema

from caselawclient.factories import IdentifierResolutionFactory, IdentifierResolutionsFactory
from caselawclient.models.identifiers.exceptions import GlobalDuplicateIdentifierException


class TestGloballyUniqueIdentifierSchema(TestIdentifierSchema):
    require_globally_unique = True


class TestGloballyUniqueIdentifier(TestIdentifier):
    schema = TestGloballyUniqueIdentifierSchema


@patch(
    "caselawclient.identifier_resolution.IDENTIFIER_NAMESPACE_MAP",
    {"test": TestGloballyUniqueIdentifier, "other-namespace": TestGloballyUniqueIdentifier},
)
class TestRequireGloballyUniqueIdentifierConstraint:
    def test_adding_id_raises_exception_if_duplicate_exists(self, mock_api_client):
        resolutions = IdentifierResolutionsFactory.build(
            [
                IdentifierResolutionFactory.build(namespace="test", value="TEST-123"),
            ]
        )
        mock_api_client.resolve_from_identifier_value.return_value = resolutions

        new_identifier = TestGloballyUniqueIdentifier(value="TEST-123")

        with pytest.raises(GlobalDuplicateIdentifierException):
            new_identifier.validate_require_globally_unique(api_client=mock_api_client)
            mock_api_client.resolve_from_identifier_value.assert_called_once_with(identifier_value="TEST-123")

    def test_adding_id_doesnt_raise_exception_if_no_resolutions(self, mock_api_client):
        resolutions = IdentifierResolutionsFactory.build([])
        mock_api_client.resolve_from_identifier_value.return_value = resolutions

        new_identifier = TestGloballyUniqueIdentifier(value="TEST-123")

        new_identifier.validate_require_globally_unique(api_client=mock_api_client)
        mock_api_client.resolve_from_identifier_value.assert_called_once_with(identifier_value="TEST-123")

    def test_adding_id_doesnt_raise_exception_if_only_match_is_not_in_namespace(self, mock_api_client):
        resolutions = IdentifierResolutionsFactory.build(
            [
                IdentifierResolutionFactory.build(namespace="other-namespace", value="TEST-123"),
            ]
        )
        mock_api_client.resolve_from_identifier_value.return_value = resolutions

        new_identifier = TestGloballyUniqueIdentifier(value="TEST-123")

        new_identifier.validate_require_globally_unique(api_client=mock_api_client)
        mock_api_client.resolve_from_identifier_value.assert_called_once_with(identifier_value="TEST-123")
