from typing import Optional

from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataFieldValue
from caselawclient.models.documents.metadata.fields.source import MetadataSource


def _claim_sort_key(claim: MetadataField) -> tuple[int, float, str]:
    """Order by source precedence, then first-seen time, then id.

    Ascending order means the last active claim is the single-value winner
    (highest source, then latest timestamp).
    """
    return (claim.source.precedence, claim.timestamp.timestamp(), claim.id)


class ResolvedMetadataField:
    """Resolved view of all claims sharing a metadata field name."""

    def __init__(self, name: str, claims: list[MetadataField]) -> None:
        self.name = name
        self._claims = sorted(claims, key=_claim_sort_key)

    @property
    def has_any_claims(self) -> bool:
        """True if any claims exist for this name, including suppressed ones."""
        return len(self._claims) > 0

    @property
    def all_claims(self) -> list[MetadataField]:
        """All claims for this name, including suppressed, lowest→highest precedence."""
        return list(self._claims)

    @property
    def claims(self) -> list[MetadataField]:
        """Active (non-suppressed) claims, lowest→highest precedence then timestamp."""
        return [claim for claim in self._claims if not claim.rejected]

    @property
    def value(self) -> Optional[MetadataFieldValue]:
        """Highest-precedence active claim value, or ``None`` if none are active.

        When multiple active claims share the winning source, the latest
        ``timestamp`` wins (editor changes are remove+add, so a new claim carries
        a newer first-seen time).
        """
        active = self.claims
        if not active:
            return None
        return active[-1].value

    @property
    def values(self) -> list[MetadataFieldValue]:
        """All active claim values across every source (multi-value resolution)."""
        return [claim.value for claim in self.claims]

    @property
    def winning_source(self) -> Optional[MetadataSource]:
        """Source of the highest-precedence active claim, if any."""
        active = self.claims
        if not active:
            return None
        return active[-1].source
