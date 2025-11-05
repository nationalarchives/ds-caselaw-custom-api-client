import pytest

from caselawclient.models.documents import Document, DocumentURIString


class TestDocumentValidation:
    def test_judgment_is_failure(self, mock_api_client):
        successful_document = Document(DocumentURIString("test/1234"), mock_api_client)
        failing_document = Document(DocumentURIString("failures/test/1234"), mock_api_client)

        successful_document.body.failed_to_parse = False
        failing_document.body.failed_to_parse = True

        assert successful_document.is_failure is False
        assert failing_document.is_failure is True

    def test_judgment_is_parked(self, mock_api_client):
        normal_document = Document(DocumentURIString("test/1234"), mock_api_client)
        parked_document = Document(DocumentURIString("parked/a1b2c3d4"), mock_api_client)

        assert normal_document.is_parked is False
        assert parked_document.is_parked is True

    def test_has_name(self, mock_api_client):
        document_with_name = Document(DocumentURIString("test/1234"), mock_api_client)
        document_with_name.body.name = "Judgment v Judgement"

        document_without_name = Document(DocumentURIString("test/1234"), mock_api_client)
        document_without_name.body.name = ""

        assert document_with_name.has_name is True
        assert document_without_name.has_name is False

    def test_has_court_is_covered_by_has_valid_court(self, mock_api_client):
        document_with_court = Document(DocumentURIString("test/1234"), mock_api_client)
        document_with_court.body.court = "UKSC"

        document_without_court = Document(DocumentURIString("test/1234"), mock_api_client)
        document_without_court.body.court = ""

        document_with_court_and_jurisdiction = Document(DocumentURIString("test/1234"), mock_api_client)
        document_with_court_and_jurisdiction.body.court = "UKFTT-GRC"
        document_with_court_and_jurisdiction.body.jurisdiction = "InformationRights"

        assert document_with_court.has_valid_court is True
        assert document_with_court_and_jurisdiction.has_valid_court is True
        assert document_without_court.has_valid_court is False

    @pytest.mark.parametrize(
        "is_failure, is_parked, is_held, has_name, has_valid_court, has_unique_content_hash, has_only_cleaned_assets, publishable, test_case",
        [
            (False, False, False, True, True, True, True, True, "Publishable"),
            (True, False, False, False, False, False, True, False, "Parser failure"),
            (
                False,
                False,
                True,
                True,
                True,
                True,
                True,
                False,
                "Held",
            ),
            (
                False,
                True,
                False,
                True,
                True,
                True,
                True,
                False,
                "Parked",
            ),
            (
                False,
                False,
                False,
                False,
                True,
                True,
                True,
                False,
                "No name",
            ),
            (False, False, False, True, False, True, True, False, "Invalid court"),
            (False, False, False, True, True, False, True, False, "Content hash not unique"),
            (False, False, False, True, True, True, False, False, "Has uncleaned asset"),
        ],
    )
    def test_document_is_publishable_conditions(
        self,
        mock_api_client,
        is_failure,
        is_held,
        is_parked,
        has_name,
        has_valid_court,
        has_unique_content_hash,
        has_only_cleaned_assets,
        publishable,
        test_case,
    ):
        mock_api_client.has_unique_content_hash.return_value = has_unique_content_hash
        document = Document(DocumentURIString(f"test/1234/{test_case.replace(' ', '_')}"), mock_api_client)
        document.is_failure = is_failure
        document.is_parked = is_parked
        document.is_held = is_held
        document.has_name = has_name
        document.has_valid_court = has_valid_court
        document.has_only_clean_assets = has_only_cleaned_assets

        assert document.is_publishable is publishable

    def test_document_validation_failure_messages_if_no_messages(self, mock_api_client):
        mock_api_client.has_unique_content_hash.return_value = True
        mock_api_client.get_judgment_xml_bytestring.return_value = b"""
            <akomaNtoso xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                        xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment><meta><identification><FRBRWork>
                <FRBRname value="Test Claimant v Test Defendant"/>
                </FRBRWork></identification></meta></judgment>
            </akomaNtoso>
        """

        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_parked = False
        document.is_held = False
        document.has_valid_court = True

        assert document.validation_failure_messages == []

    def test_judgment_validation_failure_messages_if_failing(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_failure = True
        document.is_parked = True
        document.is_held = True
        document.has_name = False
        document.has_valid_court = False

        assert document.validation_failure_messages == sorted(
            [
                "There is another document with identical content",
                "This document failed to parse",
                "This document is currently parked at a temporary URI",
                "This document is currently on hold",
                "This document has no name",
                "The court for this document is not valid",
            ],
        )
