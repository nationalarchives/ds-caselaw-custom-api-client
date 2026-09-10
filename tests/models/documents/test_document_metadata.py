from unittest.mock import Mock

import pytest

from caselawclient.models.documents.metadata.base import MultipleMetadata, SingleMetadata


class _TestSingleMetadata(SingleMetadata[str]):
    key = "test_single"
    title = "Test Single"
    description = "A test single metadata item."
    LOGIC_VERSION = 1

    @property
    def value(self) -> str:
        return "single value"


class _TestMultipleMetadata(MultipleMetadata[str]):
    key = "test_multiple"
    title = "Test Multiple"
    description = "A test multiple metadata item."
    LOGIC_VERSION = 1

    @property
    def values(self) -> list[str]:
        return ["first", "second"]


class TestMetadataBase:
    def test_single_metadata_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            SingleMetadata(Mock())  # type: ignore[abstract, unused-ignore]

    def test_multiple_metadata_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            MultipleMetadata(Mock())  # type: ignore[abstract, unused-ignore]

    def test_concrete_single_metadata_exposes_key_title_description_and_value(self):
        metadata = _TestSingleMetadata(Mock())

        assert metadata.key == "test_single"
        assert metadata.title == "Test Single"
        assert metadata.description == "A test single metadata item."
        assert metadata.editable is False
        assert metadata.value == "single value"

    def test_concrete_multiple_metadata_exposes_values(self):
        metadata = _TestMultipleMetadata(Mock())

        assert metadata.key == "test_multiple"
        assert metadata.title == "Test Multiple"
        assert metadata.description == "A test multiple metadata item."
        assert metadata.editable is False
        assert metadata.values == ["first", "second"]

    def test_editable_can_be_overridden_on_subclass(self):
        class _EditableMetadata(_TestSingleMetadata):
            editable = True

        metadata = _EditableMetadata(Mock())

        assert metadata.editable is True

    def test_concrete_metadata_must_define_logic_version(self):
        with pytest.raises(TypeError, match="must define LOGIC_VERSION"):

            class _MissingLogicVersion(SingleMetadata[str]):
                key = "missing_logic"
                title = "Missing"
                description = "Should fail."

                @property
                def value(self) -> str:
                    return "x"


class TestNameMetadata:
    def test_name_metadata_is_single_metadata_with_title_key(self):
        from caselawclient.models.documents.metadata.types.name import NameMetadata

        assert issubclass(NameMetadata, SingleMetadata)
        assert NameMetadata.key == "title"

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
        title_from_registry = document.metadata.title
        assert isinstance(title_from_registry, NameMetadata)
        assert title_from_registry.value == metadata.value

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
    def test_categories_metadata_uses_categories_key(self):
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata

        assert CategoriesMetadata.key == "categories"

    def test_categories_metadata_values_match_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata

        document = DocumentFactory.build(api_client=mock_api_client)
        assert CategoriesMetadata(document).values == document.body.categories


class TestJudgesMetadata:
    def test_judges_metadata_uses_judges_key(self):
        from caselawclient.models.documents.metadata.types.judges import JudgesMetadata

        assert JudgesMetadata.key == "judges"
        assert JudgesMetadata.title == "Judges"

    def test_judges_metadata_values_match_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentBodyFactory, DocumentFactory
        from caselawclient.models.documents.metadata.types.judges import JudgesMetadata

        body = DocumentBodyFactory.build(
            """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <header><p><judge>Judge A</judge> and <judge>Judge B</judge></p></header>
                </judgment>
            </akomaNtoso>
            """
        )
        document = DocumentFactory.build(api_client=mock_api_client, body=body)
        assert JudgesMetadata(document).values == ["Judge A", "Judge B"]
        assert document.metadata.judges.values == document.body.judges


class TestPartiesMetadata:
    def test_parties_metadata_is_multiple_with_parties_key(self):
        from caselawclient.models.documents.metadata.types.parties import PartiesMetadata

        assert issubclass(PartiesMetadata, MultipleMetadata)
        assert PartiesMetadata.key == "parties"
        assert PartiesMetadata.editable is True

    def test_parties_empty_when_no_claims_and_no_body_parties(self, mock_api_client):
        from caselawclient.factories import DocumentFactory

        document = DocumentFactory.build(api_client=mock_api_client)

        assert document.metadata.parties.values == []
        assert document.metadata.parties.values == document.body.parties

    def test_parties_metadata_values_match_document_body(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.body import DocumentBody
        from caselawclient.models.documents.metadata.fields.field import MetadataPartyValue

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <proprietary>
                            <uk:party role="Claimant">Jerry</uk:party>
                            <uk:party role="Defendant">Tom</uk:party>
                        </proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = DocumentFactory.build(api_client=mock_api_client, body=body)
        assert document.metadata.parties.values == [
            MetadataPartyValue(name="Jerry", role="Claimant"),
            MetadataPartyValue(name="Tom", role="Defendant"),
        ]
        assert document.metadata.parties.values == document.body.parties

    def test_parties_values_from_active_claims_across_sources(self, mock_api_client):
        from datetime import UTC, datetime
        from uuid import uuid4

        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.fields.collection import MetadataFieldAddResult
        from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataPartyValue
        from caselawclient.models.documents.metadata.fields.source import MetadataSource

        document = DocumentFactory.build(api_client=mock_api_client)
        timestamp = datetime(2025, 1, 1, tzinfo=UTC)
        document_party = MetadataPartyValue(name="Doc Party", role="respondent")
        external_party = MetadataPartyValue(name="Ext Party", role="appellant")

        assert (
            document.metadata_fields.add(
                MetadataField(
                    name="parties",
                    value=document_party,
                    source=MetadataSource.DOCUMENT,
                    id=str(uuid4()),
                    timestamp=timestamp,
                )
            )
            is MetadataFieldAddResult.ADDED
        )
        assert (
            document.metadata_fields.add(
                MetadataField(
                    name="parties",
                    value=external_party,
                    source=MetadataSource.EXTERNAL,
                    id=str(uuid4()),
                    timestamp=timestamp,
                )
            )
            is MetadataFieldAddResult.ADDED
        )
        assert (
            document.metadata_fields.add(
                MetadataField(
                    name="parties",
                    value=external_party,
                    source=MetadataSource.EXTERNAL,
                    id=str(uuid4()),
                    timestamp=timestamp,
                )
            )
            is MetadataFieldAddResult.ALREADY_PRESENT
        )

        assert document.metadata.parties.values == [document_party, external_party]

    def test_parties_facade_dedupes_same_party_across_sources(self, mock_api_client):
        from datetime import UTC, datetime
        from uuid import uuid4

        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataPartyValue
        from caselawclient.models.documents.metadata.fields.source import MetadataSource

        document = DocumentFactory.build(api_client=mock_api_client)
        timestamp = datetime(2025, 1, 1, tzinfo=UTC)
        shared = MetadataPartyValue(name="Acme Ltd", role="appellant")

        document.metadata_fields.add(
            MetadataField(
                name="parties",
                value=shared,
                source=MetadataSource.DOCUMENT,
                id=str(uuid4()),
                timestamp=timestamp,
            )
        )
        document.metadata_fields.add(
            MetadataField(
                name="parties",
                value=shared,
                source=MetadataSource.EXTERNAL,
                id=str(uuid4()),
                timestamp=timestamp,
            )
        )

        assert len(document.metadata_fields.by_name("parties")) == 2
        assert document.metadata.parties.values == [shared]

    def test_parties_materialise_body_claims_yanks_body_parties(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.body import DocumentBody
        from caselawclient.models.documents.metadata.fields.field import MetadataPartyValue
        from caselawclient.models.documents.metadata.fields.source import MetadataSource

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <proprietary>
                            <uk:party role="Claimant">Jerry</uk:party>
                        </proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = DocumentFactory.build(api_client=mock_api_client, body=body)
        document.metadata.parties.materialise_body_claims()

        claims = document.metadata_fields.by_name("parties")
        assert len(claims) == 1
        assert claims[0].source is MetadataSource.DOCUMENT
        assert claims[0].value == MetadataPartyValue(name="Jerry", role="Claimant")


class TestHeadnoteSummaryMetadata:
    def test_headnote_summary_is_optional_string_key(self):
        from caselawclient.models.documents.metadata.types.headnote_summary import HeadnoteSummaryMetadata

        assert issubclass(HeadnoteSummaryMetadata, SingleMetadata)
        assert HeadnoteSummaryMetadata.key == "headnote_summary"
        assert HeadnoteSummaryMetadata.editable is True

    def test_headnote_summary_none_when_no_claims(self, mock_api_client):
        from caselawclient.factories import DocumentFactory

        document = DocumentFactory.build(api_client=mock_api_client)

        assert document.metadata.headnote_summary.value is None

    def test_headnote_summary_prefers_claim_value(self, mock_api_client):
        from datetime import UTC, datetime
        from uuid import uuid4

        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataStringValue
        from caselawclient.models.documents.metadata.fields.source import MetadataSource

        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata_fields.add(
            MetadataField(
                name="headnote_summary",
                value=MetadataStringValue("  Short headnote  "),
                source=MetadataSource.EXTERNAL,
                id=str(uuid4()),
                timestamp=datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        assert document.metadata.headnote_summary.value == "Short headnote"

    def test_headnote_summary_materialise_body_claims_is_noop(self, mock_api_client):
        from caselawclient.factories import DocumentFactory

        document = DocumentFactory.build(api_client=mock_api_client)
        document.metadata.headnote_summary.materialise_body_claims()

        assert document.metadata_fields.by_name("headnote_summary") == []


class TestDocumentMetadata:
    def test_factory_built_document_metadata_exposes_typed_facades(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.registry import DocumentMetadata
        from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
        from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
        from caselawclient.models.documents.metadata.types.court import CourtMetadata
        from caselawclient.models.documents.metadata.types.date import DateMetadata
        from caselawclient.models.documents.metadata.types.headnote_summary import HeadnoteSummaryMetadata
        from caselawclient.models.documents.metadata.types.judges import JudgesMetadata
        from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
        from caselawclient.models.documents.metadata.types.name import NameMetadata
        from caselawclient.models.documents.metadata.types.parties import PartiesMetadata

        document = DocumentFactory.build(api_client=mock_api_client)

        assert isinstance(document.metadata, DocumentMetadata)
        assert isinstance(document.metadata.title, NameMetadata)
        assert isinstance(document.metadata.court, CourtMetadata)
        assert isinstance(document.metadata.jurisdiction, JurisdictionMetadata)
        assert isinstance(document.metadata.date, DateMetadata)
        assert isinstance(document.metadata.case_number, CaseNumberMetadata)
        assert isinstance(document.metadata.categories, CategoriesMetadata)
        assert isinstance(document.metadata.judges, JudgesMetadata)
        assert isinstance(document.metadata.parties, PartiesMetadata)
        assert isinstance(document.metadata.headnote_summary, HeadnoteSummaryMetadata)
        assert document.metadata.title.value == "Judgment v Judgement"
        assert document.metadata.court.value == "Court of Testing"

    def test_metadata_facades_match_field_class_registry(self, mock_api_client):
        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.registry import METADATA_FIELD_CLASSES

        document = DocumentFactory.build(api_client=mock_api_client)

        for cls in METADATA_FIELD_CLASSES:
            assert isinstance(getattr(document.metadata, cls.key), cls)

    def test_metadata_rejects_mapping_apis(self, mock_api_client):
        from caselawclient.factories import DocumentFactory

        document = DocumentFactory.build(api_client=mock_api_client)

        with pytest.raises(TypeError):
            document.metadata["title"]  # type: ignore[index, unused-ignore]
        with pytest.raises(TypeError, match="does not support membership tests"):
            _ = "title" in document.metadata
        assert not hasattr(document.metadata, "get")
        assert not hasattr(document.metadata, "keys")
        assert not hasattr(document.metadata, "values")

    def test_metadata_iterates_registered_facades(self, mock_api_client):
        from dataclasses import fields

        from caselawclient.factories import DocumentFactory
        from caselawclient.models.documents.metadata.base import Metadata
        from caselawclient.models.documents.metadata.registry import DocumentMetadata

        document = DocumentFactory.build(api_client=mock_api_client)

        facades = list(document.metadata)
        assert all(isinstance(facade, Metadata) for facade in facades)
        assert facades == [getattr(document.metadata, field.name) for field in fields(DocumentMetadata)]
