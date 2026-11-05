"""Orchestrate syncing resolved metadata claims into document body XML.

Title and work-level decision-date write-back are implemented via ``FrbrIdentificationWriter``.
Other metadata fields will extend this module or add dedicated writers as they are implemented;
there is no per-field ``write_resolved_to_body()`` hook on metadata types today.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from caselawclient.models.documents.exceptions import UnparsableDecisionDateError

from .frbr_identification_writer import FrbrIdentificationWriter

if TYPE_CHECKING:
    from caselawclient.models.documents import Document


def validate_decision_date_for_write_back(document: Document) -> None:
    """Block write-back when the work decision date is unparsable and no date claim resolves it."""
    if not document.body.supports_metadata_write_back:
        return
    if document.metadata_fields.resolve("date").has_any_claims:
        return
    if not document.body.decision_date_is_unparsable:
        return
    raw = document.body.decision_date_raw
    raise UnparsableDecisionDateError(
        f"Cannot save: work decision date {raw!r} is not a valid ISO date; "
        "fix the body XML or add a date metadata claim before saving."
    )


class BodyMetadataWriteBack:
    """Sync resolved title and decision-date metadata into Akoma Ntoso body XML."""

    def __init__(self, frbr_writer: FrbrIdentificationWriter | None = None) -> None:
        self._frbr_writer = frbr_writer or FrbrIdentificationWriter()

    def sync(self, document: Document) -> bool:
        if not document.body.supports_metadata_write_back:
            return False
        validate_decision_date_for_write_back(document)
        return self._frbr_writer.write(document)
