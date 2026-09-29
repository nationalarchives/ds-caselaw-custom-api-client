"""Orchestrate syncing resolved metadata claims into document body XML.

Title write-back is implemented via ``FrbrIdentificationWriter``. Other metadata
fields will extend this module or add dedicated writers as they are implemented;
there is no per-field ``write_resolved_to_body()`` hook on metadata types today.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .frbr_identification_writer import FrbrIdentificationWriter

if TYPE_CHECKING:
    from caselawclient.models.documents import Document


class BodyMetadataWriteBack:
    """Sync resolved title metadata into Akoma Ntoso body XML (title-only for now)."""

    def __init__(self, frbr_writer: FrbrIdentificationWriter | None = None) -> None:
        self._frbr_writer = frbr_writer or FrbrIdentificationWriter()

    def sync(self, document: Document) -> bool:
        if not document.body.supports_metadata_write_back:
            return False
        return self._frbr_writer.write(document)
