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
