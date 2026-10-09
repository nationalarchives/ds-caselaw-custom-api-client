import datetime
from unittest.mock import Mock, PropertyMock, patch

import pytest

from caselawclient.errors import DocumentNotFoundError
from caselawclient.factories import (
    DocumentBodyFactory,
    IdentifierResolutionFactory,
    IdentifierResolutionsFactory,
    JudgmentFactory,
    PressSummaryFactory,
    build_document_body_xml,
)
from caselawclient.models.documents import Document, DocumentURIString
from caselawclient.models.documents.exceptions import DocumentMergeNotPossibleError
from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataStringValue
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.versions import VersionType
from caselawclient.models.identifiers.collection import IdentifiersCollection
from caselawclient.models.identifiers.exceptions import IdentifierValidationException
from caselawclient.models.identifiers.fclid import FindCaseLawIdentifier
from caselawclient.models.identifiers.neutral_citation import NeutralCitationNumber, NeutralCitationNumberSchema
from caselawclient.models.identifiers.unpacker import unpack_all_identifiers_from_etree
from caselawclient.models.judgments import Judgment

TARGET_URI = DocumentURIString("test/2023/1")
SOURCE_URI = DocumentURIString("d-source")
OLD = datetime.datetime(2023, 1, 1, tzinfo=datetime.UTC)
NEW = datetime.datetime(2023, 6, 1, tzinfo=datetime.UTC)

REAL_DISCARD_CACHED_STATE = Document._discard_cached_state  # noqa: SLF001
REAL_RELOAD_STATE = Document._reload_state_from_marklogic  # noqa: SLF001


def _court_claim(value: str, *, source: MetadataSource = MetadataSource.EDITOR, **kwargs) -> MetadataField:
    return MetadataField("court", MetadataStringValue(value), source, **kwargs)


@pytest.fixture
def checkouts(mock_api_client):
    """MarkLogic reports, per URI, the annotation of the most recent checkout."""
    annotations: dict[str, str] = {}

    def _checkout(uri, *, annotation, **kwargs):
        annotations[uri] = annotation

    mock_api_client.checkout_judgment.side_effect = _checkout
    mock_api_client.get_judgment_checkout_status_message.side_effect = annotations.get


@pytest.fixture
def target(mock_api_client, checkouts):
    target = JudgmentFactory.build(
        uri=TARGET_URI,
        api_client=mock_api_client,
        editing_lock_held=False,
        identifiers=[FindCaseLawIdentifier(value="bcdfghjk")],
    )
    target.version_created_datetime = OLD
    target.save = Mock()  # type: ignore[method-assign]
    mock_api_client.get_document_by_uri.return_value = target
    return target


@pytest.fixture
def memory_source(mock_api_client):
    source = JudgmentFactory.build(
        uri=SOURCE_URI,
        api_client=mock_api_client,
        editing_lock_held=False,
        identifiers=[FindCaseLawIdentifier(value="mnpqrstv")],
    )
    source._persisted = False  # noqa: SLF001
    return source


@pytest.fixture
def persisted_source(mock_api_client, checkouts):
    source = JudgmentFactory.build(
        uri=SOURCE_URI,
        api_client=mock_api_client,
        editing_lock_held=False,
        identifiers=[FindCaseLawIdentifier(value="mnpqrstv")],
    )
    source.versions = [{"uri": "d-source_xml_versions/1-d-source"}]  # type: ignore[typeddict-item]
    source.version_created_datetime = NEW
    source.structured_annotation = {"type": "submission", "payload": {"tre": "data"}}  # type: ignore[typeddict-item]
    properties = {"source-name": "Source Name", "transfer-consignment-reference": "TDR-NEW"}
    mock_api_client.get_property.side_effect = lambda _uri, name: properties.get(name, "")
    return source


@pytest.fixture
def aws():
    with (
        patch("caselawclient.models.documents.copy_assets") as copy_assets,
        patch("caselawclient.models.documents.delete_documents_from_private_bucket") as delete_bucket,
    ):
        yield Mock(copy_assets=copy_assets, delete_bucket=delete_bucket)


@pytest.fixture(autouse=True)
def refresh():
    """
    The fixtures stub values that are normally read from MarkLogic (versions, timestamps and so on), so stop the
    refresh that `merge_into` does once it holds its sessions from discarding them. Tests can give `reload` a side
    effect to simulate MarkLogic having changed in the meantime.
    """
    with (
        patch.object(Document, "_reload_state_from_marklogic") as reload,
        patch.object(Document, "_discard_cached_state") as discard,
    ):
        yield Mock(reload=reload, discard=discard)


class TestMergeIntoInMemorySource:
    def test_saves_source_body_as_new_version_of_target(self, memory_source, target, mock_api_client, aws):
        result = memory_source.merge_into(
            TARGET_URI, "Merged", version_type=VersionType.SUBMISSION, automated=True, payload={"a": 1}
        )

        assert result is target
        assert target.body is memory_source.body
        target.save.assert_called_once_with(
            "Merged", version_type=VersionType.SUBMISSION, automated=True, payload={"a": 1}
        )

    def test_takes_and_releases_target_session_only(self, memory_source, target, mock_api_client, aws):
        memory_source.merge_into(TARGET_URI, "Merged")

        mock_api_client.checkout_judgment.assert_called_once()
        assert mock_api_client.checkout_judgment.call_args.args[0] == TARGET_URI
        mock_api_client.checkin_judgment_if_ours.assert_called_once()
        assert target.editing_session_token is None

    def test_does_not_touch_assets_properties_or_delete(self, memory_source, target, mock_api_client, aws):
        memory_source.merge_into(TARGET_URI, "Merged")

        aws.copy_assets.assert_not_called()
        aws.delete_bucket.assert_not_called()
        mock_api_client.delete_judgment_if_ours.assert_not_called()
        mock_api_client.set_property.assert_not_called()

    def test_payload_defaults_to_empty_without_merged_from(self, memory_source, target, aws):
        memory_source.merge_into(TARGET_URI, "Merged")

        assert target.save.call_args.kwargs["payload"] == {}

    def test_missing_target_raises(self, memory_source, mock_api_client, aws):
        mock_api_client.get_document_by_uri.side_effect = DocumentNotFoundError("nope")

        with pytest.raises(DocumentNotFoundError):
            memory_source.merge_into(TARGET_URI, "Merged")

        mock_api_client.checkout_judgment.assert_not_called()

    def test_releases_target_session_if_save_fails(self, memory_source, target, mock_api_client, aws):
        target.save.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            memory_source.merge_into(TARGET_URI, "Merged")

        mock_api_client.break_checkout_if_ours.assert_called_once()
        mock_api_client.checkin_judgment_if_ours.assert_not_called()


class TestMergeIntoPersistedSource:
    def test_cleans_up_source_after_saving(self, persisted_source, target, mock_api_client, aws):
        order = Mock()
        order.attach_mock(target.save, "save")
        order.attach_mock(aws.copy_assets, "copy_assets")
        order.attach_mock(mock_api_client.delete_judgment_if_ours, "delete")

        persisted_source.merge_into(TARGET_URI, "Merged")

        assert [c[0] for c in order.mock_calls] == ["save", "copy_assets", "delete"]
        aws.copy_assets.assert_called_once_with(SOURCE_URI, TARGET_URI, strict=True)
        aws.delete_bucket.assert_called_once_with(SOURCE_URI)

    def test_takes_sessions_on_both_documents(self, persisted_source, target, mock_api_client, aws):
        persisted_source.merge_into(TARGET_URI, "Merged")

        checked_out = [c.args[0] for c in mock_api_client.checkout_judgment.call_args_list]
        assert checked_out == [SOURCE_URI, TARGET_URI]

    def test_payload_is_inherited_and_records_origin(self, persisted_source, target, aws):
        persisted_source.merge_into(TARGET_URI, "Merged")

        assert target.save.call_args.kwargs["payload"] == {"tre": "data", "merged_from": SOURCE_URI}

    def test_explicit_payload_overrides_inherited(self, persisted_source, target, aws):
        persisted_source.merge_into(TARGET_URI, "Merged", payload={"x": 1})

        assert target.save.call_args.kwargs["payload"] == {"x": 1, "merged_from": SOURCE_URI}

    def test_source_properties_replace_target_only_when_present(self, persisted_source, target, mock_api_client, aws):
        persisted_source.merge_into(TARGET_URI, "Merged")

        assert sorted(c.args for c in mock_api_client.set_property.call_args_list) == [
            (TARGET_URI, "source-name", "Source Name"),
            (TARGET_URI, "transfer-consignment-reference", "TDR-NEW"),
        ]

    def test_failed_save_leaves_source_intact(self, persisted_source, target, mock_api_client, aws):
        target.save.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            persisted_source.merge_into(TARGET_URI, "Merged")

        aws.copy_assets.assert_not_called()
        aws.delete_bucket.assert_not_called()
        mock_api_client.delete_judgment_if_ours.assert_not_called()

    def test_failed_asset_copy_leaves_source_intact(self, persisted_source, target, mock_api_client, aws):
        aws.copy_assets.side_effect = RuntimeError("s3 down")

        with pytest.raises(RuntimeError):
            persisted_source.merge_into(TARGET_URI, "Merged")

        aws.delete_bucket.assert_not_called()
        mock_api_client.delete_judgment_if_ours.assert_not_called()


class TestMergeIntoContent:
    def test_identifiers_are_unioned_and_not_duplicated(self, memory_source, target, aws):
        ncn = NeutralCitationNumber(value="[2023] UKSC 1")
        memory_source.identifiers.add(ncn)
        target.identifiers.add(NeutralCitationNumber(value="[2023] UKSC 1"))

        memory_source.merge_into(TARGET_URI, "Merged")

        values = [(i.schema.namespace, i.value) for i in target.identifiers.values()]
        assert values.count(("ukncn", "[2023] UKSC 1")) == 1
        assert ("fclid", "bcdfghjk") in values
        assert ("fclid", "mnpqrstv") in values

    def test_single_valued_schema_deprecates_existing_target_identifier(self, memory_source, target, aws):
        memory_source.merge_into(TARGET_URI, "Merged")

        by_value = {i.value: i for i in target.identifiers.values()}
        assert by_value["bcdfghjk"].deprecated is True
        assert by_value["mnpqrstv"].deprecated is False

    def test_multi_valued_schema_keeps_existing_target_identifier(self, memory_source, target, aws):
        target.identifiers.add(NeutralCitationNumber(value="[2023] UKSC 1"))
        memory_source.identifiers.add(NeutralCitationNumber(value="[2023] UKSC 2"))

        with patch.object(NeutralCitationNumberSchema, "allow_multiple", True):
            memory_source.merge_into(TARGET_URI, "Merged")

        ncns = [i for i in target.identifiers.values() if i.schema.namespace == "ukncn"]
        assert {i.value: i.deprecated for i in ncns} == {"[2023] UKSC 1": False, "[2023] UKSC 2": False}

    def test_source_claims_are_added_to_target(self, memory_source, target, aws):
        claim = _court_claim("Elsewhere", id="source-claim")
        memory_source.metadata_fields.add(claim)

        memory_source.merge_into(TARGET_URI, "Merged")

        assert target.metadata_fields["source-claim"] is claim

    def test_equivalent_claims_are_not_duplicated(self, memory_source, target, aws):
        memory_source.metadata_fields.add(_court_claim("Elsewhere", id="source-claim"))
        target.metadata_fields.add(_court_claim("Elsewhere", id="target-claim"))

        memory_source.merge_into(TARGET_URI, "Merged")

        editor_claims = [f for f in target.metadata_fields.by_name("court") if f.source is MetadataSource.EDITOR]
        assert [f.id for f in editor_claims] == ["target-claim"]

    def test_rejected_claims_stay_rejected(self, memory_source, target, aws):
        memory_source.metadata_fields.add(_court_claim("Elsewhere", id="source-claim", rejected=True))

        memory_source.merge_into(TARGET_URI, "Merged")

        assert target.metadata_fields["source-claim"].rejected is True

    def test_target_claims_are_kept(self, memory_source, target, aws):
        target.metadata_fields.add(_court_claim("Kept", id="target-claim"))

        memory_source.merge_into(TARGET_URI, "Merged")

        assert "target-claim" in target.metadata_fields

    def test_values_only_in_the_source_body_become_claims_and_win(self, mock_api_client, target, aws):
        source = JudgmentFactory.build(
            uri=SOURCE_URI,
            api_client=mock_api_client,
            editing_lock_held=False,
            body=DocumentBodyFactory.build(court="Source Court"),
        )
        source._persisted = False  # noqa: SLF001

        source.merge_into(TARGET_URI, "Merged")

        claims = {f.value.value: f for f in target.metadata_fields.by_name("court")}
        assert set(claims) == {"Court of Testing", "Source Court"}
        assert claims["Source Court"].timestamp > claims["Court of Testing"].timestamp
        assert target.metadata_fields.resolve("court").value == MetadataStringValue("Source Court")

    def test_values_only_in_the_target_body_are_not_lost(self, memory_source, target, aws):
        memory_source.merge_into(TARGET_URI, "Merged")

        assert {f.value.value for f in target.metadata_fields.by_name("court")} == {"Court of Testing"}


class TestMergeIntoRefreshesState:
    def test_state_is_reloaded_and_rechecked_once_sessions_are_held(
        self, persisted_source, target, mock_api_client, refresh, aws
    ):
        persisted_source.merge_into(TARGET_URI, "Merged")

        refresh.reload.assert_called_once_with()
        assert refresh.discard.call_count == 2
        assert mock_api_client.checkout_judgment.call_count == 2

    def test_changes_after_the_pre_check_abort_the_merge(self, persisted_source, target, mock_api_client, refresh, aws):
        refresh.reload.side_effect = lambda: setattr(persisted_source, "has_ever_been_published", True)

        with pytest.raises(DocumentMergeNotPossibleError, match="previously been published"):
            persisted_source.merge_into(TARGET_URI, "Merged")

        target.save.assert_not_called()
        aws.copy_assets.assert_not_called()
        mock_api_client.delete_judgment_if_ours.assert_not_called()
        mock_api_client.checkin_judgment_if_ours.assert_not_called()
        assert mock_api_client.break_checkout_if_ours.call_count == 2

    def test_source_gaining_a_version_after_the_pre_check_aborts_the_merge(
        self, persisted_source, target, refresh, aws
    ):
        refresh.reload.side_effect = lambda: setattr(persisted_source, "versions", [{"uri": "a"}, {"uri": "b"}])

        with pytest.raises(DocumentMergeNotPossibleError, match="more than one version"):
            persisted_source.merge_into(TARGET_URI, "Merged")

        target.save.assert_not_called()

    def test_discard_cached_state_forgets_marklogic_values_only(self, target):
        target.__dict__["slug"] = "stale"
        target.__dict__["is_published"] = True

        REAL_DISCARD_CACHED_STATE(target)

        assert "slug" not in target.__dict__
        assert "is_published" not in target.__dict__
        assert target.uri == TARGET_URI

    def test_reload_state_rereads_body_identifiers_and_claims(self, target, mock_api_client, refresh):
        mock_api_client.get_judgment_xml_bytestring.return_value = build_document_body_xml(court="Reloaded").encode()
        mock_api_client.get_property_as_node.return_value = None
        target.identifiers.add(NeutralCitationNumber(value="[2023] UKSC 1"))
        target.metadata_fields.add(_court_claim("Unsaved"))

        REAL_RELOAD_STATE(target)

        assert target.body.court == "Reloaded"
        assert len(target.identifiers) == 0
        assert len(target.metadata_fields) == 0
        refresh.discard.assert_called_once_with()


class TestMergeIntoChecks:
    def test_cannot_merge_with_itself(self, memory_source, mock_api_client, aws):
        mock_api_client.get_document_by_uri.return_value = memory_source

        with pytest.raises(DocumentMergeNotPossibleError, match="itself"):
            memory_source.merge_into(SOURCE_URI, "Merged")

    def test_cannot_merge_into_a_version(self, memory_source, target, aws):
        target.uri = DocumentURIString("test/2023/1_xml_versions/1-1")

        with pytest.raises(DocumentMergeNotPossibleError, match="specific version"):
            memory_source.merge_into(target.uri, "Merged")

    def test_cannot_merge_a_version(self, memory_source, target, aws):
        memory_source.uri = DocumentURIString("d-source_xml_versions/1-d-source")

        with pytest.raises(DocumentMergeNotPossibleError, match="cannot be used as a merge source"):
            memory_source.merge_into(TARGET_URI, "Merged")

    def test_persisted_version_source_rejected_without_asking_marklogic_for_its_versions(
        self, persisted_source, target, aws
    ):
        persisted_source.uri = DocumentURIString("d-source_xml_versions/1-d-source")

        with (
            patch.object(Judgment, "versions", new_callable=PropertyMock) as versions,
            patch.object(Judgment, "has_ever_been_published", new_callable=PropertyMock) as published,
            pytest.raises(DocumentMergeNotPossibleError, match="cannot be used as a merge source"),
        ):
            persisted_source.merge_into(TARGET_URI, "Merged")

        versions.assert_not_called()
        published.assert_not_called()

    def test_age_check_is_skipped_when_target_is_a_version(self, persisted_source, target, aws):
        target.uri = DocumentURIString("test/2023/1_xml_versions/1-1")
        target.version_created_datetime = NEW + datetime.timedelta(days=1)

        with pytest.raises(DocumentMergeNotPossibleError) as excinfo:
            persisted_source.merge_into(target.uri, "Merged")

        assert excinfo.value.messages == ["The target document is a specific version, and cannot be merged into"]

    def test_cannot_merge_different_types(self, mock_api_client, target, aws):
        source = PressSummaryFactory.build(uri=SOURCE_URI, api_client=mock_api_client, editing_lock_held=False)
        source._persisted = False  # noqa: SLF001

        with pytest.raises(DocumentMergeNotPossibleError, match="does not match"):
            source.merge_into(TARGET_URI, "Merged")

    def test_failures_are_all_reported_and_nothing_is_written(self, mock_api_client, target, aws):
        source = PressSummaryFactory.build(uri=TARGET_URI, api_client=mock_api_client, editing_lock_held=False)
        source._persisted = False  # noqa: SLF001

        with pytest.raises(DocumentMergeNotPossibleError) as excinfo:
            source.merge_into(TARGET_URI, "Merged")

        assert len(excinfo.value.messages) == 2
        mock_api_client.checkout_judgment.assert_not_called()
        target.save.assert_not_called()

    def test_persisted_source_with_several_versions_rejected(self, persisted_source, target, aws):
        persisted_source.versions = [{"uri": "a"}, {"uri": "b"}]

        with pytest.raises(DocumentMergeNotPossibleError, match="more than one version"):
            persisted_source.merge_into(TARGET_URI, "Merged")

    def test_persisted_source_previously_published_rejected(self, persisted_source, target, aws):
        persisted_source.has_ever_been_published = True

        with pytest.raises(DocumentMergeNotPossibleError, match="previously been published"):
            persisted_source.merge_into(TARGET_URI, "Merged")

    def test_persisted_source_unsafe_to_delete_rejected(self, persisted_source, target, aws):
        persisted_source.safe_to_delete = False

        with pytest.raises(DocumentMergeNotPossibleError, match="cannot be deleted"):
            persisted_source.merge_into(TARGET_URI, "Merged")

    def test_persisted_source_older_than_target_rejected(self, persisted_source, target, mock_api_client, aws):
        persisted_source.version_created_datetime = OLD
        target.version_created_datetime = NEW

        with pytest.raises(DocumentMergeNotPossibleError, match="older than"):
            persisted_source.merge_into(TARGET_URI, "Merged")

        mock_api_client.checkout_judgment.assert_not_called()

    def test_persisted_source_newer_than_target_accepted(self, persisted_source, target, aws):
        persisted_source.merge_into(TARGET_URI, "Merged")

        target.save.assert_called_once()

    def test_in_memory_source_is_not_subject_to_age_check(self, memory_source, target, aws):
        target.version_created_datetime = NEW

        memory_source.merge_into(TARGET_URI, "Merged")

        target.save.assert_called_once()


class FakeSlugView:
    """
    A stand-in for MarkLogic's `compiled_url_slugs` SQL view, which the local test database does not materialise.

    The view is derived from the identifiers saved on each document, so this keeps that saved state per document
    and answers `resolve_from_identifier_value` from it. Saving a document's identifiers updates it and deleting a
    document removes it, as in MarkLogic, which lets the real `Document.save()` validation run against it.
    """

    def __init__(self, mock_api_client):
        self.saved: dict[str, IdentifiersCollection] = {}
        self.lookups: list[tuple[str, list[str]]] = []
        mock_api_client.resolve_from_identifier_value.side_effect = self.resolve
        mock_api_client.set_property_as_node.side_effect = self.set_property_as_node
        mock_api_client.delete_judgment_if_ours.side_effect = self.delete

    def persist(self, document) -> None:
        """Record the document's identifiers as already saved, as a copy so later edits to the object don't leak in."""
        self.saved[document.uri] = unpack_all_identifiers_from_etree(document.identifiers.as_etree)

    def resolve(self, *, identifier_value, published_only):
        assert published_only is False
        resolutions = [
            IdentifierResolutionFactory.build(
                resolution_uuid=identifier.uuid,
                document_uri=f"/{uri}.xml",
                identifier_slug=identifier.url_slug,
                published=False,
                namespace=identifier.schema.namespace,
                value=identifier.value,
            )
            for uri, identifiers in self.saved.items()
            for identifier in identifiers.values()
            if identifier.value == identifier_value
        ]
        self.lookups.append((identifier_value, [resolution.document_uri for resolution in resolutions]))
        return IdentifierResolutionsFactory.build(resolutions)

    def set_property_as_node(self, uri, name, node) -> None:
        if name == "identifiers":
            self.saved[uri] = unpack_all_identifiers_from_etree(node)

    def delete(self, uri, _session_token) -> bool:
        self.saved.pop(uri, None)
        return True


class TestMergedIdentifierValidation:
    """
    A persisted source is only deleted after the target is saved, so its identifiers are still held by the source when
    the target's identifiers are validated for saving. Merging preserves identifier uuids, so the uniqueness check
    recognises them as the same identifier rather than a clash. These run the real `Document.save()`.
    """

    @pytest.fixture
    def slug_view(self, mock_api_client):
        return FakeSlugView(mock_api_client)

    @pytest.fixture
    def saving_target(self, target, slug_view):
        del target.save  # use the real method rather than the mock the `target` fixture installs
        slug_view.persist(target)
        return target

    def test_identifiers_move_to_the_target_without_clashing_with_the_source(
        self, persisted_source, saving_target, slug_view, aws
    ):
        slug_view.persist(persisted_source)
        source_identifier = persisted_source.identifiers.of_type(FindCaseLawIdentifier)[0]

        persisted_source.merge_into(TARGET_URI, "Merged")

        # The source still held the identifier when the target was validated, so the check really was exercised.
        assert (source_identifier.value, [f"/{SOURCE_URI}.xml"]) in slug_view.lookups
        # Afterwards the identifier resolves to the target alone, under the same uuid.
        resolutions = slug_view.resolve(identifier_value=source_identifier.value, published_only=False)
        assert [(r.document_uri, r.identifier_uuid) for r in resolutions] == [
            (f"/{TARGET_URI}.xml", source_identifier.uuid)
        ]
        assert SOURCE_URI not in slug_view.saved

    def test_identifier_held_by_another_document_blocks_the_merge(
        self, persisted_source, saving_target, slug_view, mock_api_client, aws
    ):
        slug_view.persist(persisted_source)
        other = JudgmentFactory.build(
            uri=DocumentURIString("d-other"),
            api_client=mock_api_client,
            identifiers=[FindCaseLawIdentifier(value="mnpqrstv")],
        )
        slug_view.persist(other)

        with pytest.raises(IdentifierValidationException, match="must be unique"):
            persisted_source.merge_into(TARGET_URI, "Merged")

        aws.copy_assets.assert_not_called()
        aws.delete_bucket.assert_not_called()
        assert set(slug_view.saved) == {SOURCE_URI, TARGET_URI, "d-other"}
