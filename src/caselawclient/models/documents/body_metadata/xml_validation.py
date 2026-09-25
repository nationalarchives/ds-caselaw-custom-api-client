"""Validation hooks for body metadata write-back."""

from __future__ import annotations

from collections.abc import Callable

from caselawclient.xml_helpers import Element

from .frbr_identification_validation import frbr_identification_validation_failure

FrbrIdentificationValidator = Callable[[Element], str | None]
"""Return ``None`` when valid, otherwise a human-readable reason."""


def validate_frbr_identification_element(identification: Element) -> str | None:
    return frbr_identification_validation_failure(identification)
