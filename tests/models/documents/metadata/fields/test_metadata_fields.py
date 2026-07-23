from datetime import UTC, datetime

import pytest
from lxml import etree

from caselawclient.models.documents.metadata.fields.collection import MetadataFieldsCollection
from caselawclient.models.documents.metadata.fields.exceptions import (
    InvalidMetadataFieldXMLRepresentationException,
    MetadataFieldRemovalNotAllowedException,
)
from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue, MetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.metadata.fields.unpacker import (
    unpack_a_metadata_field_from_etree,
    unpack_all_metadata_fields_from_etree,
)

EARLY_TIMESTAMP = datetime(2025, 12, 17, 18, 0, 0, tzinfo=UTC)
LATE_TIMESTAMP = datetime(2025, 12, 18, 12, 0, 0, tzinfo=UTC)


class TestMetadataSource:
    def test_precedence_order(self):
        assert MetadataSource.DOCUMENT.precedence < MetadataSource.EXTERNAL.precedence
        assert MetadataSource.EXTERNAL.precedence < MetadataSource.EDITOR.precedence


class TestMetadataFieldPacking:
    def test_pack_scalar_value(self):
        field = MetadataField(
            name="title",
            value="A Judgment",
            source=MetadataSource.DOCUMENT,
            id="2d80bf1d-e3ea-452f-965c-041f4399f2dd",
            timestamp=EARLY_TIMESTAMP,
        )
        element = field.as_etree

        assert element.tag == "metadata"
        assert element.get("id") == "2d80bf1d-e3ea-452f-965c-041f4399f2dd"
        assert element.get("name") == "title"
        assert element.get("source") == "document"
        assert element.get("timestamp") == EARLY_TIMESTAMP.isoformat()
        assert element.get("rejected") == "false"
        assert element.text == "A Judgment"

    def test_pack_category_value(self):
        field = MetadataField(
            name="category",
            value=MetadataCategoryValue(name="Subcategory", parent="Category"),
            source=MetadataSource.EXTERNAL,
            id="7c4e8a91-3b2f-4d6e-9a1c-5e8f0b2d4a67",
            timestamp=EARLY_TIMESTAMP,
        )
        element = field.as_etree

        assert element.findtext("name") == "Subcategory"
        assert element.findtext("parent") == "Category"

    def test_pack_category_with_null_parent(self):
        field = MetadataField(
            name="category",
            value=MetadataCategoryValue(name="Category One", parent=None),
            source=MetadataSource.EXTERNAL,
            id="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            timestamp=EARLY_TIMESTAMP,
        )
        parent = field.as_etree.find("parent")
        assert parent is not None
        assert parent.text is None

    def test_pack_rejected(self):
        field = MetadataField(
            name="title",
            value="Wrong",
            source=MetadataSource.DOCUMENT,
            id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
            timestamp=EARLY_TIMESTAMP,
            rejected=True,
        )
        assert field.as_etree.get("rejected") == "true"


class TestMetadataFieldUnpacking:
    def test_unpack_scalar(self):
        xml = etree.fromstring(
            '<metadata id="2d80bf1d-e3ea-452f-965c-041f4399f2dd" name="title" source="document" '
            f'timestamp="{EARLY_TIMESTAMP.isoformat()}" rejected="false">A Judgment</metadata>'
        )
        field = unpack_a_metadata_field_from_etree(xml)

        assert field.id == "2d80bf1d-e3ea-452f-965c-041f4399f2dd"
        assert field.name == "title"
        assert field.source is MetadataSource.DOCUMENT
        assert field.value == "A Judgment"
        assert field.timestamp == EARLY_TIMESTAMP
        assert field.rejected is False

    def test_unpack_category(self):
        xml = etree.fromstring(
            '<metadata id="7c4e8a91-3b2f-4d6e-9a1c-5e8f0b2d4a67" name="category" source="external" '
            f'timestamp="{EARLY_TIMESTAMP.isoformat()}">'
            "<name>Subcategory</name><parent>Category</parent></metadata>"
        )
        field = unpack_a_metadata_field_from_etree(xml)

        assert isinstance(field.value, MetadataCategoryValue)
        assert field.value.name == "Subcategory"
        assert field.value.parent == "Category"

    def test_unpack_category_empty_parent(self):
        xml = etree.fromstring(
            '<metadata id="a1b2c3d4-e5f6-7890-abcd-ef1234567890" name="category" source="external" '
            f'timestamp="{EARLY_TIMESTAMP.isoformat()}">'
            "<name>Category One</name><parent/></metadata>"
        )
        field = unpack_a_metadata_field_from_etree(xml)

        assert isinstance(field.value, MetadataCategoryValue)
        assert field.value.parent is None

    def test_unpack_rejected(self):
        xml = etree.fromstring(
            '<metadata id="f47ac10b-58cc-4372-a567-0e02b2c3d479" name="title" source="document" '
            f'timestamp="{EARLY_TIMESTAMP.isoformat()}" rejected="true">Wrong</metadata>'
        )
        assert unpack_a_metadata_field_from_etree(xml).rejected is True

    def test_unpack_missing_id_raises(self):
        xml = etree.fromstring(
            f'<metadata name="title" source="document" timestamp="{EARLY_TIMESTAMP.isoformat()}">A Judgment</metadata>'
        )
        with pytest.raises(InvalidMetadataFieldXMLRepresentationException, match="id"):
            unpack_a_metadata_field_from_etree(xml)

    def test_unpack_missing_name_raises(self):
        xml = etree.fromstring(
            '<metadata id="9b2c8e4f-1a3d-4c5e-8f7a-6b0d9e2c1a34" source="document" '
            f'timestamp="{EARLY_TIMESTAMP.isoformat()}">X</metadata>'
        )
        with pytest.raises(InvalidMetadataFieldXMLRepresentationException, match="name"):
            unpack_a_metadata_field_from_etree(xml)

    def test_unpack_missing_source_raises(self):
        xml = etree.fromstring(
            '<metadata id="9b2c8e4f-1a3d-4c5e-8f7a-6b0d9e2c1a34" name="title" '
            f'timestamp="{EARLY_TIMESTAMP.isoformat()}">X</metadata>'
        )
        with pytest.raises(InvalidMetadataFieldXMLRepresentationException, match="source"):
            unpack_a_metadata_field_from_etree(xml)

    def test_unpack_missing_timestamp_raises(self):
        xml = etree.fromstring(
            '<metadata id="9b2c8e4f-1a3d-4c5e-8f7a-6b0d9e2c1a34" name="title" source="document">X</metadata>'
        )
        with pytest.raises(InvalidMetadataFieldXMLRepresentationException, match="timestamp"):
            unpack_a_metadata_field_from_etree(xml)

    def test_unpack_unparsable_timestamp_raises(self):
        xml = etree.fromstring(
            '<metadata id="9b2c8e4f-1a3d-4c5e-8f7a-6b0d9e2c1a34" name="title" source="document" '
            'timestamp="not-a-datetime">X</metadata>'
        )
        with pytest.raises(InvalidMetadataFieldXMLRepresentationException, match="unparsable timestamp"):
            unpack_a_metadata_field_from_etree(xml)

    def test_unpack_unknown_source_raises(self):
        xml = etree.fromstring(
            '<metadata id="9b2c8e4f-1a3d-4c5e-8f7a-6b0d9e2c1a34" name="title" source="mystery" '
            f'timestamp="{EARLY_TIMESTAMP.isoformat()}">X</metadata>'
        )
        with pytest.raises(InvalidMetadataFieldXMLRepresentationException, match="unknown source"):
            unpack_a_metadata_field_from_etree(xml)

    def test_unpack_empty_category_name_raises(self):
        xml = etree.fromstring(
            '<metadata id="9b2c8e4f-1a3d-4c5e-8f7a-6b0d9e2c1a34" name="category" source="external" '
            f'timestamp="{EARLY_TIMESTAMP.isoformat()}"><name/><parent/></metadata>'
        )
        with pytest.raises(InvalidMetadataFieldXMLRepresentationException, match="category name"):
            unpack_a_metadata_field_from_etree(xml)

    def test_unpack_none_returns_empty_collection(self):
        assert unpack_all_metadata_fields_from_etree(None) == MetadataFieldsCollection()

    def test_roundtrip(self):
        original = MetadataFieldsCollection()
        original.add(
            MetadataField(
                name="title",
                value="Judgment",
                source=MetadataSource.DOCUMENT,
                id="c0ffee00-dead-beef-cafe-0123456789ab",
                timestamp=EARLY_TIMESTAMP,
            )
        )
        original.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="Cat", parent=None),
                source=MetadataSource.EXTERNAL,
                id="1e2f3a4b-5c6d-7e8f-9012-3456789abcde",
                timestamp=LATE_TIMESTAMP,
                rejected=True,
            )
        )

        unpacked = unpack_all_metadata_fields_from_etree(original.as_etree)

        assert set(unpacked.keys()) == set(original.keys())
        assert unpacked["c0ffee00-dead-beef-cafe-0123456789ab"].value == "Judgment"
        assert unpacked["c0ffee00-dead-beef-cafe-0123456789ab"].timestamp == EARLY_TIMESTAMP
        assert unpacked["1e2f3a4b-5c6d-7e8f-9012-3456789abcde"].rejected is True
        category = unpacked["1e2f3a4b-5c6d-7e8f-9012-3456789abcde"].value
        assert isinstance(category, MetadataCategoryValue)
        assert category.name == "Cat"
        assert category.parent is None


class TestMetadataFieldsResolution:
    def test_single_value_uses_highest_precedence(self):
        collection = MetadataFieldsCollection()
        collection.add(
            MetadataField(
                name="title",
                value="From document",
                source=MetadataSource.DOCUMENT,
                id="10d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
                timestamp=EARLY_TIMESTAMP,
            )
        )
        collection.add(
            MetadataField(
                name="title",
                value="From editor",
                source=MetadataSource.EDITOR,
                id="71e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f80",
                timestamp=EARLY_TIMESTAMP,
            )
        )
        collection.add(
            MetadataField(
                name="title",
                value="From external",
                source=MetadataSource.EXTERNAL,
                id="45b8c9d0-e1f2-4a3b-4c5d-6e7f8091a2b3",
                timestamp=EARLY_TIMESTAMP,
            )
        )

        resolved = collection.resolve("title")
        assert resolved.value == "From editor"
        assert resolved.winning_source is MetadataSource.EDITOR

    def test_same_source_prefers_latest_timestamp(self):
        collection = MetadataFieldsCollection()
        collection.add(
            MetadataField(
                name="title",
                value="Older editor title",
                source=MetadataSource.EDITOR,
                id="71e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f80",
                timestamp=EARLY_TIMESTAMP,
            )
        )
        collection.add(
            MetadataField(
                name="title",
                value="Newer editor title",
                source=MetadataSource.EDITOR,
                id="81e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f80",
                timestamp=LATE_TIMESTAMP,
            )
        )

        assert collection.resolve("title").value == "Newer editor title"

    def test_winning_source_is_none_when_empty(self):
        assert MetadataFieldsCollection().resolve("title").winning_source is None

    def test_multi_value_returns_all_non_suppressed(self):
        collection = MetadataFieldsCollection()
        collection.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="A"),
                source=MetadataSource.DOCUMENT,
                id="d3a7b8c9-d0e1-4f2a-3b4c-5d6e7f8091a2",
                timestamp=EARLY_TIMESTAMP,
            )
        )
        collection.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="B"),
                source=MetadataSource.EXTERNAL,
                id="e3a7b8c9-d0e1-4f2a-3b4c-5d6e7f8091a2",
                timestamp=EARLY_TIMESTAMP,
            )
        )
        collection.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="C"),
                source=MetadataSource.EDITOR,
                id="f3a7b8c9-d0e1-4f2a-3b4c-5d6e7f8091a2",
                timestamp=EARLY_TIMESTAMP,
            )
        )
        collection.add(
            MetadataField(
                name="category",
                value=MetadataCategoryValue(name="Rejected"),
                source=MetadataSource.EXTERNAL,
                id="04a7b8c9-d0e1-4f2a-3b4c-5d6e7f8091a2",
                timestamp=EARLY_TIMESTAMP,
                rejected=True,
            )
        )

        values = collection.resolve("category").values
        assert [value.name for value in values if isinstance(value, MetadataCategoryValue)] == ["A", "B", "C"]

    def test_suppressed_only_is_empty(self):
        collection = MetadataFieldsCollection()
        collection.add(
            MetadataField(
                name="title",
                value="Wrong",
                source=MetadataSource.DOCUMENT,
                id="60d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
                timestamp=EARLY_TIMESTAMP,
                rejected=True,
            )
        )
        resolved = collection.resolve("title")
        assert resolved.has_any_claims is True
        assert resolved.value is None
        assert resolved.values == []
        assert len(resolved.all_claims) == 1


class TestMetadataFieldsMutation:
    def test_reject_soft_deletes(self):
        collection = MetadataFieldsCollection()
        field = MetadataField(
            name="category",
            value=MetadataCategoryValue(name="Bad"),
            source=MetadataSource.EXTERNAL,
            id="14a7b8c9-d0e1-4f2a-3b4c-5d6e7f8091a2",
            timestamp=EARLY_TIMESTAMP,
        )
        collection.add(field)

        collection.reject(field.id)

        assert field.rejected is True
        assert field.id in collection
        assert collection.resolve("category").values == []

    def test_remove_editor_claim(self):
        collection = MetadataFieldsCollection()
        field = MetadataField(
            name="category",
            value=MetadataCategoryValue(name="Editor cat"),
            source=MetadataSource.EDITOR,
            id="24a7b8c9-d0e1-4f2a-3b4c-5d6e7f8091a2",
            timestamp=EARLY_TIMESTAMP,
        )
        collection.add(field)

        collection.remove(field.id)

        assert field.id not in collection

    def test_remove_external_claim_raises(self):
        collection = MetadataFieldsCollection()
        field = MetadataField(
            name="category",
            value=MetadataCategoryValue(name="External cat"),
            source=MetadataSource.EXTERNAL,
            id="34a7b8c9-d0e1-4f2a-3b4c-5d6e7f8091a2",
            timestamp=EARLY_TIMESTAMP,
        )
        collection.add(field)

        with pytest.raises(MetadataFieldRemovalNotAllowedException):
            collection.remove(field.id)

        assert field.id in collection
