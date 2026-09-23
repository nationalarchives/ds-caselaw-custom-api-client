"""Orchestrate syncing resolved metadata claims into document body XML."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .frbr_identification_writer import FrbrIdentificationWriter

if TYPE_CHECKING:
    from caselawclient.models.documents import Document


class BodyMetadataWriteBack:
    """Sync resolved metadata into Akoma Ntoso body XML blocks."""

    def __init__(self, frbr_writer: FrbrIdentificationWriter | None = None) -> None:
        self._frbr_writer = frbr_writer or FrbrIdentificationWriter()

    def sync(self, document: Document) -> bool:
        if not document.body.supports_metadata_write_back:
            return False
        return self._frbr_writer.write(document)
