"""Import-time metadata materialisation version derived from per-field LOGIC_VERSION."""

from __future__ import annotations

import hashlib
import json

from caselawclient.models.documents.metadata.registry import METADATA_FIELD_CLASSES

LATEST_METADATA_MATERIALISATION_VERSION_PROPERTY = "latest_metadata_materialisation_version"


def metadata_logic_versions() -> dict[str, int]:
    """Return the shape descriptor ``{metadata_key: LOGIC_VERSION}`` (sorted keys)."""
    return {cls.key: cls.LOGIC_VERSION for cls in sorted(METADATA_FIELD_CLASSES, key=lambda c: c.key)}


def compute_metadata_materialisation_version(versions: dict[str, int] | None = None) -> str:
    """Stable hash of the metadata shape (keys and logic versions, not claim values)."""
    shape = versions if versions is not None else metadata_logic_versions()
    payload = json.dumps(shape, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# Computed once at import — callers compare documents against this constant.
CURRENT_METADATA_MATERIALISATION_VERSION = compute_metadata_materialisation_version()


def document_needs_metadata_materialisation(stored_version: str | None) -> bool:
    """True when a document has never been materialised, or was materialised under older rules."""
    return not stored_version or stored_version != CURRENT_METADATA_MATERIALISATION_VERSION
