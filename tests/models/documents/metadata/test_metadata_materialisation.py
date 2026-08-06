from datetime import UTC, date, datetime
from uuid import uuid4

from caselawclient.factories import DocumentBodyFactory, DocumentFactory
from caselawclient.models.documents.metadata.fields.field import MetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.metadata.materialisation import (
    CURRENT_METADATA_MATERIALISATION_VERSION,
    LATEST_METADATA_MATERIALISATION_VERSION_PROPERTY,
    compute_metadata_materialisation_version,
    document_needs_metadata_materialisation,
    metadata_logic_versions,
)

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
        document.metadata["title"].materialise_body_claims()

        claims = document.metadata_fields.by_name("title")
        assert len(claims) == 1
        assert claims[0].value == "Body Title"
        assert claims[0].source is MetadataSource.DOCUMENT

    def test_materialise_is_idempotent_for_same_document_value(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Body Title"),
        )
        document.metadata["title"].materialise_body_claims()
        first_id = document.metadata_fields.by_name("title")[0].id
        document.metadata["title"].materialise_body_claims()

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
        document.metadata["title"].materialise_body_claims()

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
        document.metadata["jurisdiction"].materialise_body_claims()
        document.metadata["case_number"].materialise_body_claims()

        assert document.metadata_fields.by_name("jurisdiction") == []
        assert document.metadata_fields.by_name("case_number") == []

    def test_date_materialises_isoformat(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(document_date_as_string="2023-02-03"),
        )
        document.metadata["date"].materialise_body_claims()

        claims = document.metadata_fields.by_name("date")
        assert len(claims) == 1
        assert claims[0].value == "2023-02-03"
        assert isinstance(claims[0].value, str)
        assert date.fromisoformat(claims[0].value) == date(2023, 2, 3)

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
        document.metadata["title"].materialise_body_claims()

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
        document.metadata["categories"].materialise_body_claims()

        values = {
            (claim.value.name, claim.value.parent)  # type: ignore[union-attr]
            for claim in document.metadata_fields.by_name("categories")
        }
        assert values == {("Parent", None), ("Child", "Parent")}


class TestDocumentMaterialiseMetadataClaims:
    def test_materialise_persists_fields_and_version(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="Saved Title", court="Saved Court"),
        )

        document.materialise_metadata_claims()

        mock_api_client.set_property_as_node.assert_called_once()
        uri, property_name, _tree = mock_api_client.set_property_as_node.call_args.args
        assert uri == document.uri
        assert property_name == "metadata_fields"
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
