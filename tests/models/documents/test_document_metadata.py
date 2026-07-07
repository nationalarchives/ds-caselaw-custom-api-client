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
    def test_metadata_is_dict_keyed_by_metadata_type(self, mock_api_client):
        from caselawclient.factories import DocumentFactory

        document = DocumentFactory.build(api_client=mock_api_client)

        assert isinstance(document.metadata, dict)
        assert document.metadata

    def test_metadata_keys_match_registered_types(self, mock_api_client):
        from caselawclient.factories import DocumentFactory

        document = DocumentFactory.build(api_client=mock_api_client)

        assert set(document.metadata.keys()) == {
            "name",
            "court",
            "jurisdiction",
            "date",
            "case_number",
            "categories",
        }

    def test_metadata_entries_are_expected_types(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
        from caselawclient.models.documents.metadata.types.court import CourtMetadata
        from caselawclient.models.documents.metadata.types.date import DateMetadata
        from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(api_client=mock_api_client)

        assert isinstance(document.metadata["name"], NameMetadata)
        assert isinstance(document.metadata["court"], CourtMetadata)
        assert isinstance(document.metadata["jurisdiction"], JurisdictionMetadata)
        assert isinstance(document.metadata["date"], DateMetadata)
        assert isinstance(document.metadata["case_number"], CaseNumberMetadata)
        assert isinstance(document.metadata["categories"], CategoriesMetadata)

    def test_metadata_name_value_matches_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        name_metadata = document.metadata["name"]
        assert isinstance(name_metadata, NameMetadata)
        assert name_metadata.value == document.body.name

    def test_metadata_categories_values_match_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        categories_metadata = document.metadata["categories"]
        assert isinstance(categories_metadata, CategoriesMetadata)
        assert categories_metadata.values == document.body.categories

    def test_metadata_get_returns_none_for_unknown_key(self, mock_api_client):
        from caselawclient.factories import DocumentFactory

        document = DocumentFactory.build(api_client=mock_api_client)

        assert document.metadata.get("nonexistent") is None

    def test_metadata_values_yields_all_registered_instances(self, mock_api_client):
        from caselawclient.factories import DocumentFactory

        document = DocumentFactory.build(api_client=mock_api_client)

        assert len(list(document.metadata.values())) == 6
