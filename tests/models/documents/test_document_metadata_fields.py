from datetime import UTC, datetime
from uuid import uuid4

import pytest
from lxml import etree

from caselawclient.factories import DocumentFactory
from caselawclient.models.documents.metadata.fields.exceptions import MetadataFieldValidationException
from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue, MetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.metadata.fields.unpacker import unpack_all_metadata_fields_from_etree
from caselawclient.types import SuccessFailureMessageTuple

TIMESTAMP = datetime(2025, 12, 17, 18, 0, 0, tzinfo=UTC)


def _id() -> str:
    """Generate a claim id for tests where the specific value does not matter."""
    return str(uuid4())


class TestDocumentMetadataFieldsLoadSave:
    def test_document_loads_empty_metadata_fields_when_property_missing(self, mock_api_client):
        mock_api_client.get_property_as_node.return_value = None
        document = DocumentFactory.build(api_client=mock_api_client)

        assert list(document.metadata_fields.values()) == []

    def test_document_loads_metadata_fields_from_property(self, mock_api_client):
        claim_id = _id()
        xml = etree.fromstring(
            "<metadata_fields>"
            f'<metadata id="{claim_id}" name="title" source="editor" '
            f'timestamp="{TIMESTAMP.isoformat()}" rejected="false">'
            "From fields"
            "</metadata>"
            "</metadata_fields>"
        )

        def get_property_as_node(_uri: str, name: str):
            if name == "metadata_fields":
                return xml
            return None

        mock_api_client.get_property_as_node.side_effect = get_property_as_node
        document = DocumentFactory.build(api_client=mock_api_client)

        assert document.metadata_fields.resolve("title").value == "From fields"

    def test_save_metadata_fields_writes_property(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value="Saved title",
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        document.save_metadata_fields()

        mock_api_client.set_property_as_node.assert_called_once()
        uri, property_name, tree = mock_api_client.set_property_as_node.call_args.args
        assert uri == document.uri
        assert property_name == "metadata_fields"
        assert unpack_all_metadata_fields_from_etree(tree).resolve("title").value == "Saved title"

    def test_validate_metadata_fields_returns_success_failure_tuple(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        field = MetadataField(
            name="title",
            value="Saved title",
            source=MetadataSource.EDITOR,
            id=_id(),
            timestamp=TIMESTAMP,
        )
        document.metadata_fields["wrong-key"] = field

        result = document.validate_metadata_fields()

        assert result == SuccessFailureMessageTuple(
            False,
            [f"Key of {field} in MetadataFieldsCollection is wrong-key not {field.id}"],
        )

    def test_save_metadata_fields_rejects_mismatched_keys(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        field = MetadataField(
            name="title",
            value="Saved title",
            source=MetadataSource.EDITOR,
            id=_id(),
            timestamp=TIMESTAMP,
        )
        document.metadata_fields["wrong-key"] = field

        with pytest.raises(MetadataFieldValidationException, match="wrong-key"):
            document.save_metadata_fields()

        mock_api_client.set_property_as_node.assert_not_called()


class TestDocumentMetadataFacadePrefersFields:
    def test_name_falls_back_to_body_when_no_claims(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Body Name"),
        )

        assert document.metadata["title"].value == "Body Name"

    def test_name_prefers_metadata_fields(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Body Name"),
        )
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value="Fields Name",
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        assert document.metadata["title"].value == "Fields Name"

    def test_name_suppressed_only_is_empty(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Body Name"),
        )
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value="Rejected Name",
                source=MetadataSource.DOCUMENT,
                id=_id(),
                timestamp=TIMESTAMP,
                rejected=True,
            )
        )

        assert document.metadata["title"].value == ""

    def test_categories_prefers_all_non_suppressed_fields(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(),
        )
        document.metadata_fields.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="From document"),
                source=MetadataSource.DOCUMENT,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )
        document.metadata_fields.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="From external"),
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )
        document.metadata_fields.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="Rejected"),
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
                rejected=True,
            )
        )

        assert [category.name for category in document.metadata["category"].values] == [
            "From document",
            "From external",
        ]

    def test_categories_dedupe_same_name_from_multiple_sources(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="Shared", parent=None),
                source=MetadataSource.DOCUMENT,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )
        document.metadata_fields.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="Shared", parent=None),
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        categories = document.metadata["category"].values
        assert len(categories) == 1
        assert categories[0].name == "Shared"

    def test_categories_build_parent_child_tree(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="Parent", parent=None),
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )
        document.metadata_fields.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="Child", parent="Parent"),
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        categories = document.metadata["category"].values
        assert len(categories) == 1
        assert categories[0].name == "Parent"
        assert [child.name for child in categories[0].subcategories] == ["Child"]

    def test_date_parses_field_value(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value="2024-06-15",
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        assert document.metadata["date"].as_string == "2024-06-15"

    def test_date_suppressed_only_is_none(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value="2024-06-15",
                source=MetadataSource.DOCUMENT,
                id=_id(),
                timestamp=TIMESTAMP,
                rejected=True,
            )
        )

        assert document.metadata["date"].value is None
        assert document.metadata["date"].as_string == ""

    def test_date_unparsable_field_value_is_none(self, mock_api_client):
        from caselawclient.models.documents.body import UnparsableDate

        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value="not-a-date",
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        with pytest.warns(UnparsableDate, match="Unparsable date"):
            assert document.metadata["date"].value is None

    def test_date_empty_string_field_value_is_none(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value="",
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        assert document.metadata["date"].value is None

    def test_case_number_prefers_metadata_fields(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="case_number",
                value="ABC-123",
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        assert document.metadata["case_number"].value == "ABC-123"

    def test_case_number_suppressed_only_is_none(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="case_number",
                value="ABC-123",
                source=MetadataSource.DOCUMENT,
                id=_id(),
                timestamp=TIMESTAMP,
                rejected=True,
            )
        )

        assert document.metadata["case_number"].value is None

    def test_case_number_non_string_value_raises(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="case_number",
                value=MetadataCategoryValue(name="not-a-case-number"),
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        with pytest.raises(TypeError, match="Expected string metadata value for 'case_number'"):
            _ = document.metadata["case_number"].value

    def test_court_prefers_metadata_fields(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(court="Body Court"),
        )
        document.metadata_fields.add(
            MetadataField(
                name="court",
                value="Fields Court",
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        assert document.metadata["court"].value == "Fields Court"

    def test_court_suppressed_only_is_empty(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(court="Body Court"),
        )
        document.metadata_fields.add(
            MetadataField(
                name="court",
                value="Rejected Court",
                source=MetadataSource.DOCUMENT,
                id=_id(),
                timestamp=TIMESTAMP,
                rejected=True,
            )
        )

        assert document.metadata["court"].value == ""

    def test_court_non_string_value_raises(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="court",
                value=MetadataCategoryValue(name="not-a-court"),
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        with pytest.raises(TypeError, match="Expected string metadata value for 'court'"):
            _ = document.metadata["court"].value

    def test_jurisdiction_prefers_metadata_fields(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(jurisdiction="Body Jurisdiction"),
        )
        document.metadata_fields.add(
            MetadataField(
                name="jurisdiction",
                value="Fields Jurisdiction",
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        assert document.metadata["jurisdiction"].value == "Fields Jurisdiction"

    def test_jurisdiction_suppressed_only_is_empty(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory

        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(jurisdiction="Body Jurisdiction"),
        )
        document.metadata_fields.add(
            MetadataField(
                name="jurisdiction",
                value="Rejected",
                source=MetadataSource.DOCUMENT,
                id=_id(),
                timestamp=TIMESTAMP,
                rejected=True,
            )
        )

        assert document.metadata["jurisdiction"].value == ""

    def test_jurisdiction_non_string_value_raises(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="jurisdiction",
                value=MetadataCategoryValue(name="not-a-jurisdiction"),
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        with pytest.raises(TypeError, match="Expected string metadata value for 'jurisdiction'"):
            _ = document.metadata["jurisdiction"].value

    def test_title_non_string_value_raises(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value=MetadataCategoryValue(name="not-a-title"),
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        with pytest.raises(TypeError, match="Expected string metadata value for 'title'"):
            _ = document.metadata["title"].value

    def test_categories_orphan_child_without_parent_claim_is_omitted(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="Orphan", parent="Missing Parent"),
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )

        assert document.metadata["category"].values == []

    def test_metadata_contains_rejects_non_string_keys(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)

        assert 123 not in document.metadata
