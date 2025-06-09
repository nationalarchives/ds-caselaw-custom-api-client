from unittest.mock import patch

import pytest
from test_identifiers import TestIdentifier, TestIdentifierSchema

from caselawclient.factories import IdentifierResolutionFactory, IdentifierResolutionsFactory
from caselawclient.models.documents import Document
from caselawclient.models.identifiers.exceptions import (
    GlobalDuplicateIdentifierException,
    IdentifierNotValidForDocumentTypeException,
)


class TestGloballyUniqueIdentifierSchema(TestIdentifierSchema):
    require_globally_unique = True


class TestGloballyUniqueIdentifier(TestIdentifier):
    schema = TestGloballyUniqueIdentifierSchema


class TestNotLimitedToDocumentTypeIdentifierSchema(TestIdentifierSchema):
    document_types = None


class TestNotLimitedToDocumentTypeIdentifier(TestIdentifier):
    schema = TestNotLimitedToDocumentTypeIdentifierSchema


class TestLimitedToJudgmentDocumentTypeIdentifierSchema(TestIdentifierSchema):
    document_types = ["TestCorrectDocumentType"]


class TestLimitedToJudgmentDocumentTypeIdentifier(TestIdentifier):
    schema = TestLimitedToJudgmentDocumentTypeIdentifierSchema


class TestCorrectDocumentType(Document):
    __test__ = False


class TestIncorrectDocumentType(Document):
    __test__ = False


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


class TestDocumentTypesConstraint:
    def test_validate_valid_for_document_type_if_document_types_is_none(self):
        new_identifier = TestNotLimitedToDocumentTypeIdentifier(value="TEST-123")
        new_identifier.validate_valid_for_document_type(TestCorrectDocumentType)
        new_identifier.validate_valid_for_document_type(TestIncorrectDocumentType)

    def test_validate_valid_for_document_type_if_correct_document_type(self):
        new_identifier = TestLimitedToJudgmentDocumentTypeIdentifier(value="TEST-123")
        new_identifier.validate_valid_for_document_type(TestCorrectDocumentType)

    def test_validate_valid_for_document_type_if_incorrect_document_type(self):
        new_identifier = TestLimitedToJudgmentDocumentTypeIdentifier(value="TEST-123")
        with pytest.raises(IdentifierNotValidForDocumentTypeException):
            new_identifier.validate_valid_for_document_type(TestIncorrectDocumentType)
