from datetime import UTC, datetime
from uuid import uuid4

from caselawclient.factories import DocumentBodyFactory, DocumentFactory
from caselawclient.models.documents.metadata.fields.field import MetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource

TIMESTAMP = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)


def _id() -> str:
    return str(uuid4())


def _body_with_judges(*names: str) -> object:
    judges_xml = "".join(f"<judge>{name}</judge>" for name in names)
    return DocumentBodyFactory.build(
        f"""
        <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
            <judgment>
                <header><p>{judges_xml}</p></header>
            </judgment>
        </akomaNtoso>
        """
    )


class TestJudgesMetadataEditing:
    def test_materialise_body_claims_yanks_body_names(self, mock_api_client):
        document = DocumentFactory.build(
            api_client=mock_api_client,
            body=_body_with_judges("Judge A", "Judge B"),
        )
        judges = document.metadata["judges"]

        judges.materialise_body_claims()

        assert [claim.value for claim in document.metadata_fields.by_name("judges")] == [
            "Judge A",
            "Judge B",
        ]
        assert all(claim.source is MetadataSource.DOCUMENT for claim in document.metadata_fields.by_name("judges"))
        assert judges.values == ["Judge A", "Judge B"]

    def test_materialise_body_claims_is_noop_when_claims_exist(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client, body=_body_with_judges("Body Judge"))
        document.metadata_fields.add(
            MetadataField(
                name="judges",
                value="Claim Judge",
                source=MetadataSource.EXTERNAL,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )
        document.metadata["judges"].materialise_body_claims()
        assert [claim.value for claim in document.metadata_fields.by_name("judges")] == ["Claim Judge"]

    def test_add_editor_judge_yanks_then_adds(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client, body=_body_with_judges("Body Judge"))
        document.metadata["judges"].add_editor_judge("Editor Judge")

        claims = document.metadata_fields.by_name("judges")
        assert len(claims) == 2
        assert claims[0].source is MetadataSource.DOCUMENT
        assert claims[0].value == "Body Judge"
        assert claims[1].source is MetadataSource.EDITOR
        assert claims[1].value == "Editor Judge"
        assert document.metadata["judges"].values == ["Body Judge", "Editor Judge"]

    def test_suppress_document_claim_rejects(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client, body=_body_with_judges("Judge A", "Judge B"))
        judges = document.metadata["judges"]
        judges.materialise_body_claims()
        claim_a = next(claim for claim in document.metadata_fields.by_name("judges") if claim.value == "Judge A")

        judges.suppress_claim(claim_a.id)

        assert claim_a.rejected is True
        assert judges.values == ["Judge B"]
        # Body must not resurrect Judge A
        assert "Judge A" not in judges.values

    def test_suppress_editor_claim_hard_removes(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="judges",
                value="Editor Judge",
                source=MetadataSource.EDITOR,
                id=_id(),
                timestamp=TIMESTAMP,
            )
        )
        claim_id = next(iter(document.metadata_fields.by_name("judges"))).id
        document.metadata["judges"].suppress_claim(claim_id)
        assert document.metadata_fields.by_name("judges") == []

    def test_restore_rejected_document_claim(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client, body=_body_with_judges("Judge A"))
        judges = document.metadata["judges"]
        judges.materialise_body_claims()
        claim = document.metadata_fields.by_name("judges")[0]
        judges.suppress_claim(claim.id)
        assert judges.values == []

        judges.restore_claim(claim.id)
        assert judges.values == ["Judge A"]
