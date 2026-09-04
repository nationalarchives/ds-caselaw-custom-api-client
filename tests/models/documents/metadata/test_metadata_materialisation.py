from datetime import UTC, date, datetime
from unittest.mock import ANY, PropertyMock, patch
from uuid import uuid4

import pytest

from caselawclient.factories import DocumentBodyFactory, DocumentFactory, JudgmentFactory
from caselawclient.models.documents.metadata.base import Metadata
from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue, MetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.metadata.materialisation import (
    CURRENT_METADATA_MATERIALISATION_VERSION,
    LATEST_METADATA_MATERIALISATION_VERSION_PROPERTY,
    compute_metadata_materialisation_version,
    document_needs_metadata_materialisation,
    metadata_logic_versions,
)
from caselawclient.types import DocumentCategory

TIMESTAMP = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)


def _id() -> str:
    return str(uuid4())


class TestMetadataMaterialisationVersion:
    def test_current_version_matches_recomputed_hash(self):
        assert compute_metadata_materialisation_version() == CURRENT_METADATA_MATERIALISATION_VERSION

    def test_version_changes_when_logic_version_bumps(self):
        bumped = metadata_logic_versions()
        bumped["title"] = bumped["title"] + 1
        assert compute_metadata_materialisation_version(bumped) != CURRENT_METADATA_MATERIALISATION_VERSION

    def test_document_needs_materialisation_when_missing_or_stale(self):
        assert document_needs_metadata_materialisation(None) is True
        assert document_needs_metadata_materialisation("") is True
        assert document_needs_metadata_materialisation("stale") is True
        assert document_needs_metadata_materialisation(CURRENT_METADATA_MATERIALISATION_VERSION) is False


class TestMaterialiseBodyClaims:
    def test_title_materialises_document_claim(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Body Title"),
        )
        document.metadata.title.materialise_body_claims()

        claims = document.metadata_fields.by_name("title")
        assert len(claims) == 1
        assert claims[0].value == "Body Title"
        assert claims[0].source is MetadataSource.DOCUMENT

    def test_materialise_is_idempotent_for_same_document_value(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Body Title"),
        )
        document.metadata.title.materialise_body_claims()
        first_id = document.metadata_fields.by_name("title")[0].id
        document.metadata.title.materialise_body_claims()

        claims = document.metadata_fields.by_name("title")
        assert len(claims) == 1
        assert claims[0].id == first_id

    def test_editor_claim_does_not_block_document_materialisation(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Body Title"),
        )
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value="Editor Title",
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )
        document.metadata.title.materialise_body_claims()

        claims = document.metadata_fields.by_name("title")
        assert {(c.source, c.value) for c in claims} == {
            (MetadataSource.EDITOR, "Editor Title"),
            (MetadataSource.DOCUMENT, "Body Title"),
        }

    def test_skips_empty_body_values(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(jurisdiction="", case_number=""),
        )
        document.metadata.jurisdiction.materialise_body_claims()
        document.metadata.case_number.materialise_body_claims()

        assert document.metadata_fields.by_name("jurisdiction") == []
        assert document.metadata_fields.by_name("case_number") == []

    def test_strips_whitespace_when_materialising(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="  Body Title  "),
        )
        document.metadata.title.materialise_body_claims()

        claims = document.metadata_fields.by_name("title")
        assert len(claims) == 1
        assert claims[0].value == "Body Title"

    def test_skips_whitespace_only_string(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="   "),
        )
        document.metadata.title.materialise_body_claims()
        assert document.metadata_fields.by_name("title") == []

    def test_skips_none_case_number(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.body.__dict__["case_number"] = None
        document.metadata.case_number.materialise_body_claims()
        assert document.metadata_fields.by_name("case_number") == []

    def test_date_materialises_isoformat(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(document_date_as_string="2023-02-03"),
        )
        document.metadata.date.materialise_body_claims()

        claims = document.metadata_fields.by_name("date")
        assert len(claims) == 1
        assert claims[0].value == "2023-02-03"
        assert isinstance(claims[0].value, str)
        assert date.fromisoformat(claims[0].value) == date(2023, 2, 3)

    def test_skips_missing_document_date(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(document_date_as_string=None),
        )
        document.metadata.date.materialise_body_claims()
        assert document.metadata_fields.by_name("date") == []

    def test_base_materialise_body_claims_raises(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        with pytest.raises(NotImplementedError, match="does not implement materialise_body_claims"):
            Metadata.materialise_body_claims(document.metadata.title)

    def test_does_not_resurrect_rejected_document_claim(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Body Title"),
        )
        rejected = MetadataField(
            name="title",
            value="Body Title",
            source=MetadataSource.DOCUMENT,
            id=_id(),
            timestamp=TIMESTAMP,
            rejected=True,
        )
        document.metadata_fields.add(rejected)
        document.metadata.title.materialise_body_claims()

        claims = document.metadata_fields.by_name("title")
        assert len(claims) == 1
        assert claims[0].id == rejected.id
        assert claims[0].rejected is True

    def test_categories_materialise_flat_claim_values(self, mock_api_client):
        categories_xml = DocumentBodyFactory.build(
            """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                        xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification><FRBRWork>
                            <FRBRname value="Name"/>
                            <FRBRdate date="2023-02-03"/>
                        </FRBRWork></identification>
                        <proprietary>
                            <uk:court>Court</uk:court>
                            <uk:category>Parent</uk:category>
                            <uk:category parent="Parent">Child</uk:category>
                        </proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = DocumentFactory.build(api_client=mock_api_client, body=categories_xml)
        document.metadata.categories.materialise_body_claims()

        values = {
            (claim.value.name, claim.value.parent)
            for claim in document.metadata_fields.by_name("categories")
            if isinstance(claim.value, MetadataCategoryValue)
        }
        assert values == {("Parent", None), ("Child", "Parent")}

    def test_skips_empty_category_names_from_body(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        with patch.object(
            type(document.body),
            "categories",
            new_callable=PropertyMock,
            return_value=[DocumentCategory(name="")],
        ):
            document.metadata.categories.materialise_body_claims()

        assert document.metadata_fields.by_name("categories") == []

    def test_strips_whitespace_only_category_parent(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        with patch.object(
            type(document.body),
            "categories",
            new_callable=PropertyMock,
            return_value=[
                DocumentCategory(
                    name="   ",
                    subcategories=[DocumentCategory(name="Child")],
                )
            ],
        ):
            document.metadata.categories.materialise_body_claims()

        values = {
            (claim.value.name, claim.value.parent)
            for claim in document.metadata_fields.by_name("categories")
            if isinstance(claim.value, MetadataCategoryValue)
        }
        assert values == {("Child", None)}


class TestDocumentSaveStructuredMetadataToMarklogic:
    def test_save_persists_structured_metadata_fields_and_version(self, mock_api_client):
        document = JudgmentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Saved Title", court="Saved Court"),
        )

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml"),
        ):
            document.save(message="Persist metadata")

        mock_api_client.set_property_as_node.assert_any_call(document.uri, "metadata_fields", ANY)
        mock_api_client.set_property.assert_any_call(
            document.uri,
            LATEST_METADATA_MATERIALISATION_VERSION_PROPERTY,
            CURRENT_METADATA_MATERIALISATION_VERSION,
        )
        assert document.metadata_fields.resolve("title").value == "Saved Title"
        assert document.metadata_fields.resolve("court").value == "Saved Court"

    def test_needs_metadata_materialisation(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        mock_api_client.get_property.return_value = ""
        assert document.needs_metadata_materialisation is True

        mock_api_client.get_property.return_value = CURRENT_METADATA_MATERIALISATION_VERSION
        assert document.needs_metadata_materialisation is False
