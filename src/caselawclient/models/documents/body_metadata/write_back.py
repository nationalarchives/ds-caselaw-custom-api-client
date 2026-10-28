"""Orchestrate syncing resolved metadata claims into document body XML.

Title write-back is implemented via ``FrbrIdentificationWriter`` (``meta``);
judge names via ``HeaderJudgesWriter`` (``header`` ``judge`` elements only).
These writers must not modify the document narrative (``judgmentBody`` /
``mainBody`` text). Other metadata fields will add dedicated writers as they
are implemented; there is no per-field ``write_resolved_to_body()`` hook on
metadata types today.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .frbr_identification_writer import FrbrIdentificationWriter
from .header_judges_writer import HeaderJudgesWriter

if TYPE_CHECKING:
    from caselawclient.models.documents import Document


class BodyMetadataWriteBack:
    """Sync resolved metadata into Akoma Ntoso body XML."""

    def __init__(
        self,
        frbr_writer: FrbrIdentificationWriter | None = None,
        header_judges_writer: HeaderJudgesWriter | None = None,
    ) -> None:
        self._frbr_writer = frbr_writer or FrbrIdentificationWriter()
        self._header_judges_writer = header_judges_writer or HeaderJudgesWriter()

    def sync(self, document: Document) -> bool:
        changed = False
        if document.body.supports_metadata_write_back:
            changed = self._frbr_writer.write(document)
        if self._header_judges_writer.write(document):
            changed = True
        return changed
