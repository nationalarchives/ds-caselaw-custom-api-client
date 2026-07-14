from unittest.mock import Mock

import pytest

from caselawclient.models.documents.metadata.base import MultipleMetadata, SingleMetadata


class _TestSingleMetadata(SingleMetadata[str]):
    key = "test_single"
    title = "Test Single"
    description = "A test single metadata item."

    @property
    def value(self) -> str:
        return "single value"


class _TestMultipleMetadata(MultipleMetadata[str]):
    key = "test_multiple"
    title = "Test Multiple"
    description = "A test multiple metadata item."

    @property
    def values(self) -> list[str]:
        return ["first", "second"]


class TestMetadataBase:
    def test_single_metadata_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            SingleMetadata(Mock())  # type: ignore[abstract]

    def test_multiple_metadata_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            MultipleMetadata(Mock())  # type: ignore[abstract]

    def test_concrete_single_metadata_exposes_key_title_description_and_value(self):
        metadata = _TestSingleMetadata(Mock())

        assert metadata.key == "test_single"
        assert metadata.title == "Test Single"
        assert metadata.description == "A test single metadata item."
        assert metadata.value == "single value"

    def test_concrete_multiple_metadata_exposes_values(self):
        metadata = _TestMultipleMetadata(Mock())

        assert metadata.key == "test_multiple"
        assert metadata.title == "Test Multiple"
        assert metadata.description == "A test multiple metadata item."
        assert metadata.values == ["first", "second"]


class TestNameMetadata:
    def test_name_metadata_is_single_metadata_with_name_key(self):
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        assert issubclass(NameMetadata, SingleMetadata)
        assert NameMetadata.key == "name"

    def test_name_metadata_value_reads_from_xml(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory, DocumentFactory
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Custom Case Name"),
        )
        metadata = NameMetadata(document)

        assert metadata.value == "Custom Case Name"
        assert document.body.name == metadata.value
        name_from_registry = document.metadata.name
        assert isinstance(name_from_registry, NameMetadata)
        assert name_from_registry.value == metadata.value

    def test_name_metadata_value_matches_document_body_name(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        metadata = NameMetadata(document)

        assert metadata.value == document.body.name

    def test_name_metadata_has_title_and_description(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        metadata = NameMetadata(document)

        assert metadata.title
        assert metadata.description


class TestCourtMetadata:
    def test_court_metadata_value_matches_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.court import CourtMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        assert CourtMetadata(document).value == document.body.court


class TestJurisdictionMetadata:
    def test_jurisdiction_metadata_value_matches_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        assert JurisdictionMetadata(document).value == document.body.jurisdiction


class TestDateMetadata:
    def test_date_metadata_value_reads_from_xml(self, mock_api_client):
        import datetime

        from caselawclient.factories import DocumentBodyFactory, DocumentFactory
        from caselawclient.models.documents.metadata.types.date import DateMetadata

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(document_date_as_string="2023-02-03"),
        )
        metadata = DateMetadata(document)

        assert metadata.value == datetime.date(2023, 2, 3)
        assert metadata.as_string == "2023-02-03"
        assert str(metadata) == "2023-02-03"
        assert document.body.document_date_as_date == metadata.value

    def test_date_metadata_warns_on_unparsable_date(self):
        from caselawclient.factories import DocumentBodyFactory, DocumentFactory
        from caselawclient.models.documents.body import UnparsableDate
        from caselawclient.models.documents.metadata.types.date import DateMetadata

        document = DocumentFactory.build(
            body=DocumentBodyFactory.build(document_date_as_string="kitten"),
        )
        metadata = DateMetadata(document)

        with pytest.warns(UnparsableDate):
            assert metadata.value is None
        assert metadata.as_string == ""
        assert str(metadata) == ""

    def test_date_metadata_value_matches_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.date import DateMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        assert DateMetadata(document).value == document.body.document_date_as_date


class TestCaseNumberMetadata:
    def test_case_number_metadata_value_matches_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        assert CaseNumberMetadata(document).value == document.body.case_number


class TestCategoriesMetadata:
    def test_categories_metadata_values_match_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        assert CategoriesMetadata(document).values == document.body.categories


class TestDocumentMetadata:
    def test_factory_built_document_metadata_reads_from_xml(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.court import CourtMetadata
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(api_client=mock_api_client)

        name_metadata = document.metadata.name
        court_metadata = document.metadata.court
        assert isinstance(name_metadata, NameMetadata)
        assert isinstance(court_metadata, CourtMetadata)
        assert name_metadata.value == "Judgment v Judgement"
        assert court_metadata.value == "Court of Testing"

    def test_metadata_is_document_metadata_registry(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.registry import DocumentMetadataRegistry

        document = DocumentFactory.build(api_client=mock_api_client)

        assert isinstance(document.metadata, DocumentMetadataRegistry)

    def test_metadata_entries_are_expected_types(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
        from caselawclient.models.documents.metadata.types.court import CourtMetadata
        from caselawclient.models.documents.metadata.types.date import DateMetadata
        from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(api_client=mock_api_client)

        assert isinstance(document.metadata.name, NameMetadata)
        assert isinstance(document.metadata.court, CourtMetadata)
        assert isinstance(document.metadata.jurisdiction, JurisdictionMetadata)
        assert isinstance(document.metadata.date, DateMetadata)
        assert isinstance(document.metadata.case_number, CaseNumberMetadata)
        assert isinstance(document.metadata.categories, CategoriesMetadata)

    def test_metadata_name_value_matches_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        name_metadata = document.metadata.name
        assert isinstance(name_metadata, NameMetadata)
        assert name_metadata.value == document.body.name

    def test_metadata_categories_values_match_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        categories_metadata = document.metadata.categories
        assert isinstance(categories_metadata, CategoriesMetadata)
        assert categories_metadata.values == document.body.categories

    def test_metadata_registry_exposes_all_registered_fields(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
        from caselawclient.models.documents.metadata.types.court import CourtMetadata
        from caselawclient.models.documents.metadata.types.date import DateMetadata
        from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(api_client=mock_api_client)

        assert isinstance(document.metadata.name, NameMetadata)
        assert isinstance(document.metadata.court, CourtMetadata)
        assert isinstance(document.metadata.jurisdiction, JurisdictionMetadata)
        assert isinstance(document.metadata.date, DateMetadata)
        assert isinstance(document.metadata.case_number, CaseNumberMetadata)
        assert isinstance(document.metadata.categories, CategoriesMetadata)
