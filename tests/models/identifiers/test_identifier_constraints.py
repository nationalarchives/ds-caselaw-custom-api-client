from unittest.mock import patch

from test_identifiers import TestIdentifier, TestIdentifierSchema

from caselawclient.factories import IdentifierResolutionFactory, IdentifierResolutionsFactory
from caselawclient.models.documents import Document
from caselawclient.types import SuccessFailureMessageTuple


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
    def test_adding_id_if_duplicate_exists(self, mock_api_client):
        resolutions = IdentifierResolutionsFactory.build(
            [
                IdentifierResolutionFactory.build(namespace="test", value="TEST-123"),
            ]
        )
        mock_api_client.resolve_from_identifier_value.return_value = resolutions

        new_identifier = TestGloballyUniqueIdentifier(value="TEST-123")

        validation = new_identifier.validate_require_globally_unique(api_client=mock_api_client)
        mock_api_client.resolve_from_identifier_value.assert_called_once_with(identifier_value="TEST-123")

        assert validation.success is False
        assert validation.messages == ['Identifiers in scheme "test" must be unique; "TEST-123" already exists!']

    def test_adding_id_if_no_resolutions(self, mock_api_client):
        resolutions = IdentifierResolutionsFactory.build([])
        mock_api_client.resolve_from_identifier_value.return_value = resolutions

        new_identifier = TestGloballyUniqueIdentifier(value="TEST-123")

        validation = new_identifier.validate_require_globally_unique(api_client=mock_api_client)
        mock_api_client.resolve_from_identifier_value.assert_called_once_with(identifier_value="TEST-123")

        assert validation.success is True
        assert validation.messages == []

    def test_adding_id_if_only_match_is_not_in_namespace(self, mock_api_client):
        resolutions = IdentifierResolutionsFactory.build(
            [
                IdentifierResolutionFactory.build(namespace="other-namespace", value="TEST-123"),
            ]
        )
        mock_api_client.resolve_from_identifier_value.return_value = resolutions

        new_identifier = TestGloballyUniqueIdentifier(value="TEST-123")

        validation = new_identifier.validate_require_globally_unique(api_client=mock_api_client)
        mock_api_client.resolve_from_identifier_value.assert_called_once_with(identifier_value="TEST-123")

        assert validation.success is True
        assert validation.messages == []


class TestDocumentTypesConstraint:
    def test_validate_valid_for_document_type_if_document_types_is_none(self):
        new_identifier = TestNotLimitedToDocumentTypeIdentifier(value="TEST-123")
        validation_1 = new_identifier.validate_valid_for_document_type(TestCorrectDocumentType)
        validation_2 = new_identifier.validate_valid_for_document_type(TestIncorrectDocumentType)

        assert validation_1.success is True
        assert validation_1.messages == []

        assert validation_2.success is True
        assert validation_2.messages == []

    def test_validate_valid_for_document_type_if_correct_document_type(self):
        new_identifier = TestLimitedToJudgmentDocumentTypeIdentifier(value="TEST-123")
        validation = new_identifier.validate_valid_for_document_type(TestCorrectDocumentType)

        assert validation.success is True
        assert validation.messages == []

    def test_validate_valid_for_document_type_if_incorrect_document_type(self):
        new_identifier = TestLimitedToJudgmentDocumentTypeIdentifier(value="TEST-123")
        validation = new_identifier.validate_valid_for_document_type(TestIncorrectDocumentType)

        assert validation.success is False
        assert validation.messages == [
            'Document type "TestIncorrectDocumentType" is not accepted for identifier schema "Test Schema"'
        ]


class TestPerformAllValidations:
    def test_perform_all_validations_runs_expected_validations(self, mock_api_client):
        """Make sure that perform_all_validations is actually running the validations we expect."""
        identifier = TestIdentifier(uuid="id-1", value="TEST-123")

        with (
            patch.object(identifier, "validate_require_globally_unique") as mock_validate_require_globally_unique,
            patch.object(identifier, "validate_valid_for_document_type") as mock_validate_valid_for_document_type,
        ):
            mock_validate_require_globally_unique.return_value = SuccessFailureMessageTuple(True, [])
            mock_validate_valid_for_document_type.return_value = SuccessFailureMessageTuple(True, [])

            identifier.perform_all_validations(document_type=Document, api_client=mock_api_client)

            mock_validate_require_globally_unique.assert_called_once_with(api_client=mock_api_client)
            mock_validate_valid_for_document_type.assert_called_once_with(document_type=Document)

    def test_perform_all_validations_bubbles_success_or_failure_on_all_success(self, mock_api_client):
        """Make sure that perform_all_validations bubbles the success/failure state and messages when everything passes."""
        identifier = TestIdentifier(uuid="id-1", value="TEST-123")

        with (
            patch.object(identifier, "validate_require_globally_unique") as mock_validate_require_globally_unique,
            patch.object(identifier, "validate_valid_for_document_type") as mock_validate_valid_for_document_type,
        ):
            mock_validate_require_globally_unique.return_value = SuccessFailureMessageTuple(True, [])
            mock_validate_valid_for_document_type.return_value = SuccessFailureMessageTuple(True, [])

            validations = identifier.perform_all_validations(document_type=Document, api_client=mock_api_client)

            mock_validate_require_globally_unique.assert_called_once_with(api_client=mock_api_client)
            mock_validate_valid_for_document_type.assert_called_once_with(document_type=Document)

            assert validations.success is True
            assert validations.messages == []

    def test_perform_all_validations_bubbles_success_or_failure_on_single_failure(self, mock_api_client):
        """Make sure that perform_all_validations bubbles the success/failure state and messages when there is a single failure."""
        identifier = TestIdentifier(uuid="id-1", value="TEST-123")

        with (
            patch.object(identifier, "validate_require_globally_unique") as mock_validate_require_globally_unique,
            patch.object(identifier, "validate_valid_for_document_type") as mock_validate_valid_for_document_type,
        ):
            mock_validate_require_globally_unique.return_value = SuccessFailureMessageTuple(
                False, ["Global unique validation failure"]
            )
            mock_validate_valid_for_document_type.return_value = SuccessFailureMessageTuple(True, [])

            validations = identifier.perform_all_validations(document_type=Document, api_client=mock_api_client)

            mock_validate_require_globally_unique.assert_called_once_with(api_client=mock_api_client)
            mock_validate_valid_for_document_type.assert_called_once_with(document_type=Document)

            assert validations.success is False
            assert validations.messages == ["Global unique validation failure"]

    def test_perform_all_validations_bubbles_success_or_failure_on_multiple_failure(self, mock_api_client):
        """Make sure that perform_all_validations bubbles the success/failure state and messages when there are multiple failures."""
        identifier = TestIdentifier(uuid="id-1", value="TEST-123")

        with (
            patch.object(identifier, "validate_require_globally_unique") as mock_validate_require_globally_unique,
            patch.object(identifier, "validate_valid_for_document_type") as mock_validate_valid_for_document_type,
        ):
            mock_validate_require_globally_unique.return_value = SuccessFailureMessageTuple(
                False, ["Global unique validation failure"]
            )
            mock_validate_valid_for_document_type.return_value = SuccessFailureMessageTuple(
                False, ["Valid for type validation failure", "Further failure message"]
            )

            validations = identifier.perform_all_validations(document_type=Document, api_client=mock_api_client)

            mock_validate_require_globally_unique.assert_called_once_with(api_client=mock_api_client)
            mock_validate_valid_for_document_type.assert_called_once_with(document_type=Document)

            assert validations.success is False
            assert validations.messages == [
                "Global unique validation failure",
                "Valid for type validation failure",
                "Further failure message",
            ]
