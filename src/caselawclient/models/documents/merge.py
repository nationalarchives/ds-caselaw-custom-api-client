from __future__ import annotations

import datetime
import logging
from contextlib import ExitStack
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from caselawclient.models.documents.body_metadata.akn import (
    FRBR_EXPRESSION_XPATH,
    FRBR_MANIFESTATION_XPATH,
    FRBR_WORK_XPATH,
)
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.versions import VersionType
from caselawclient.models.utilities.aws import copy_assets
from caselawclient.types import DocumentURIString, SuccessFailureMessageTuple

if TYPE_CHECKING:
    from caselawclient.models.documents import Document

logger = logging.getLogger(__name__)

MERGED_PROPERTIES = (
    "source-organisation",
    "source-name",
    "source-email",
    "transfer-consignment-reference",
    "transfer-received-at",
    "parser-run-id",
)
""" MarkLogic properties describing where a document came from; when merging, a persisted source's values replace the target's. """


class DocumentMerge:
    """Merge a source document into an existing persisted target.

    Prefer ``document.merge_into(...)``; this class holds the implementation so
    ``Document`` stays focused on document state.
    """

    def __init__(self, source: Document) -> None:
        self.source = source

    def check_can_merge_into(self, target: Document) -> SuccessFailureMessageTuple:
        """Can ``source`` be merged into ``target``?

        Checks that need MarkLogic state only run when the source is persisted.
        """
        source = self.source
        messages: list[str] = []

        if source.uri == target.uri:
            messages.append("You cannot merge a document with itself")
        if source.is_version:
            messages.append("This document is a specific version, and cannot be used as a merge source")
        if target.is_version:
            messages.append("The target document is a specific version, and cannot be merged into")
        if type(source) is not type(target):
            messages.append(
                f"The type of {source.uri} ({type(source).document_noun}) does not match "
                f"the type of {target.uri} ({type(target).document_noun})"
            )

        # These queries only make sense for managed documents; MarkLogic errors if asked about a version's versions.
        if source._persisted and not source.is_version:  # noqa: SLF001
            if len(source.versions) > 1:
                messages.append("This document has more than one version")
            if source.has_ever_been_published:
                messages.append("This document has previously been published")
            if not source.safe_to_delete:
                messages.append("This document cannot be deleted because it is published")
            if not target.is_version and source.version_created_datetime < target.version_created_datetime:
                messages.append(f"The document at {source.uri} is older than the latest version of {target.uri}")

        return SuccessFailureMessageTuple(not messages, messages)

    def into(
        self,
        target_uri: DocumentURIString,
        message: str,
        *,
        version_type: VersionType = VersionType.SUBMISSION,
        automated: bool = False,
        payload: dict[str, Any] | None = None,
    ) -> Document:
        """
        Merge the source into the existing document at ``target_uri``, which becomes a new version of that document.

        The target must already be persisted, as MarkLogic's own versioning preserves its history. The source may
        be in memory only or already persisted. If persisted, its ingest properties (see ``MERGED_PROPERTIES``) replace
        the target's, its S3 assets are copied to the target, and it is deleted once everything else has succeeded; a
        failure before that point therefore leaves a duplicate rather than losing data.

        The target keeps all its identifiers and metadata claims; the source's are added to them. Where a schema
        allows only one non-deprecated identifier and the values differ, the target's is deprecated. Metadata held
        only in either document's body is turned into claims first, so neither body's values are lost; where the
        two disagree, the source wins. Newly synthesised target body claims are ranked below the source's DOCUMENT
        claims so an older stored source claim is not overwritten by a just-materialised target body value.
        FRBR this/uri values on the saved body are rewritten to the target URI, so a source's expression and
        manifestation identity is not stored on the target.

        This method takes its own editing sessions on the target (and on the source, if persisted). Once they are
        held the target is reloaded and the checks are repeated against fresh state. For a persisted source,
        identifiers and metadata claims are also re-read from MarkLogic (then any local-only additions reapplied),
        so a concurrent ``save_identifiers`` / ``save_metadata_fields`` is not lost; the body may still carry
        unsaved in-memory edits. A persisted source must still have a single version at that point.

        :param target_uri: The URI of the existing document to merge into.
        :param message: Human-readable message describing the merge, stored on the new version.
        :param payload: Optional structured data stored on the version annotation. If omitted and the source is
            persisted, the payload of its latest version is used. If persisted, ``merged_from`` is added to it.

        :return: The updated target document.

        :raises DocumentNotFoundError: There is no document at ``target_uri``.
        :raises DocumentMergeNotPossibleError: The documents failed the checks required to merge them.
        """
        from caselawclient.models.documents import Document
        from caselawclient.models.documents.exceptions import DocumentMergeNotPossibleError

        source = self.source
        if type(source) is Document:
            raise TypeError("Use a concrete document class such as Judgment or PressSummary to merge.")

        target = source.api_client.get_document_by_uri(target_uri)

        validation = self.check_can_merge_into(target)
        if not validation.success:
            raise DocumentMergeNotPossibleError(validation.messages)

        merge_payload = self._build_merge_payload(payload)

        with ExitStack() as sessions:
            if source._persisted:  # noqa: SLF001
                sessions.enter_context(source.editing_session())
            sessions.enter_context(target.editing_session())
            self._merge_while_locked(
                target,
                message,
                version_type=version_type,
                automated=automated,
                payload=merge_payload,
            )

        target._discard_cached_state()  # noqa: SLF001

        return target

    def _build_merge_payload(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        source = self.source
        merge_payload: dict[str, Any] = dict(payload) if payload is not None else {}
        if not source._persisted:  # noqa: SLF001
            return merge_payload

        if payload is None:
            try:
                merge_payload = dict(source.structured_annotation.get("payload") or {})
            except ValidationError:
                logger.warning("Could not read the version annotation of %s; not inheriting its payload", source.uri)
        merge_payload["merged_from"] = source.uri
        return merge_payload

    def _merge_while_locked(
        self,
        target: Document,
        message: str,
        *,
        version_type: VersionType,
        automated: bool,
        payload: dict[str, Any],
    ) -> None:
        from caselawclient.models.documents.exceptions import DocumentMergeNotPossibleError

        source = self.source

        # Anything read before the sessions were held may be stale.
        target._reload_state_from_marklogic()  # noqa: SLF001
        source._discard_cached_state()  # noqa: SLF001
        if source._persisted:  # noqa: SLF001
            self._reload_source_collections_preserving_local_edits()

        validation = self.check_can_merge_into(target)
        if not validation.success:
            raise DocumentMergeNotPossibleError(validation.messages)

        self._materialise_body_claims_for_merge(target)

        target.body = source.body
        self._rewrite_frbr_identity(target)
        self._merge_identifiers_into(target)
        for metadata_field in source.metadata_fields.values():
            target.metadata_fields.add(metadata_field)

        target.save(message, version_type=version_type, automated=automated, payload=payload)

        if source._persisted:  # noqa: SLF001
            self._hand_over_to(target)

    def _reload_source_collections_preserving_local_edits(self) -> None:
        """Re-read identifiers and metadata from MarkLogic, then reapply local-only additions.

        ``save_identifiers`` / ``save_metadata_fields`` do not create a new XML version, so the single-version
        check alone cannot detect a concurrent property save. The body is left alone so intentional unsaved
        body edits still merge.
        """
        source = self.source
        local_identifiers = list(source.identifiers.values())
        local_claims = list(source.metadata_fields.values())

        source._initialise_identifiers()  # noqa: SLF001
        source._initialise_metadata_fields()  # noqa: SLF001

        for identifier in local_identifiers:
            if not source.identifiers.contains(identifier):
                source.identifiers.add(identifier)

        for claim in local_claims:
            source.metadata_fields.add(claim)

    def _materialise_body_claims_for_merge(self, target: Document) -> None:
        """Turn body-only metadata into claims on both documents, with the source winning ties.

        A claim is only taken from a body when materialisation adds one. Target first so that, when both sides
        synthesise a claim in this call, the source's later timestamp wins. Newly synthesised target DOCUMENT
        claims are then ranked just below any source DOCUMENT claim for the same field, so a pre-existing source
        claim is not beaten by a target body value that only became a claim during this merge.
        """
        source = self.source
        before_ids = set(target.metadata_fields)
        target._convert_body_claims_to_structured_metadata()  # noqa: SLF001
        newly_synthesised = [
            claim
            for claim_id, claim in target.metadata_fields.items()
            if claim_id not in before_ids and claim.source is MetadataSource.DOCUMENT
        ]

        source._convert_body_claims_to_structured_metadata()  # noqa: SLF001

        for claim in newly_synthesised:
            source_document_claims = [
                candidate
                for candidate in source.metadata_fields.by_name(claim.name)
                if candidate.source is MetadataSource.DOCUMENT and not candidate.rejected
            ]
            if not source_document_claims:
                continue
            earliest = min(candidate.timestamp for candidate in source_document_claims)
            claim.timestamp = earliest - datetime.timedelta(microseconds=1)

    def _rewrite_frbr_identity(self, target: Document) -> None:
        """Point existing FRBR this/uri values at ``target``.

        These are the same three URI forms ``set_judgment_this_uri`` writes after a move. Elements the source
        body does not have are left absent. The content hash ignores ``akn:meta``, so this does not invalidate it.
        """
        document_uri = target.uri.lstrip("/")
        base = "https://caselaw.nationalarchives.gov.uk"
        values_by_block = {
            FRBR_WORK_XPATH: f"{base}/id/{document_uri}",
            FRBR_EXPRESSION_XPATH: f"{base}/{document_uri}",
            FRBR_MANIFESTATION_XPATH: f"{base}/{document_uri}/data.xml",
        }
        xml = target.body._xml  # noqa: SLF001
        for block_xpath, value in values_by_block.items():
            for element_name in ("FRBRthis", "FRBRuri"):
                for node in xml.get_xpath_nodes(f"{block_xpath}/akn:{element_name}"):
                    xml.set_element_attribute(node, "value", value)
        target.body._invalidate_cached_properties()  # noqa: SLF001

    def _merge_identifiers_into(self, target: Document) -> None:
        """
        Add the source's identifiers to ``target``'s, skipping any with the same value and schema.

        Where a schema permits only one non-deprecated identifier, the target's existing one is deprecated so the
        incoming one is preferred; nothing is removed.
        """
        for identifier in self.source.identifiers.values():
            if target.identifiers.contains(identifier):
                continue

            if not identifier.deprecated and not identifier.schema.allow_multiple:
                for existing in target.identifiers.values():
                    if existing.schema is identifier.schema:
                        existing.deprecated = True

            target.identifiers.add(identifier)

    def _hand_over_to(self, target: Document) -> None:
        """
        Move the persisted source's ingest properties and S3 assets to ``target``, then delete the source.

        Deletion is last, so a failure leaves a duplicate rather than losing data.
        """
        source = self.source
        for property_name in MERGED_PROPERTIES:
            value = source.api_client.get_property(source.uri, property_name)
            if value:
                source.api_client.set_property(target.uri, property_name, value)
        copy_assets(source.uri, target.uri, strict=True)
        source.delete()
