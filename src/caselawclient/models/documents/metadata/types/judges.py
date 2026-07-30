from caselawclient.models.documents.metadata.base import MultipleMetadata
from caselawclient.models.documents.metadata.fields.exceptions import MetadataFieldRemovalNotAllowedException
from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataFieldValue
from caselawclient.models.documents.metadata.fields.source import MetadataSource


def judge_names_from_field_values(values: list[MetadataFieldValue]) -> list[str]:
    """Extract unique judge name strings from metadata claim values.

    Non-string claim values are ignored. Duplicate names are de-duplicated with
    first-seen order winning.
    """
    judges: list[str] = []

    for value in values:
        if not isinstance(value, str):
            continue
        name = value.strip()
        if not name or name in judges:
            continue
        judges.append(name)

    return judges


class JudgesMetadata(MultipleMetadata[str]):
    key = "judges"
    title = "Judges"
    description = "A list of the names of the judges (or equivalent for the body) involved in any particular case."
    editable = True

    @property
    def values(self) -> list[str]:
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return self.document.body.judges
        return judge_names_from_field_values(resolved.values)

    def materialise_body_claims(self) -> None:
        """Yank body judge names into DOCUMENT claims when no claims exist yet.

        After this, resolution is claim-based and soft-delete can suppress names
        without the body fallback resurrecting them.
        """
        resolved = self._resolve_claims()
        if resolved.has_any_claims:
            return

        for name in self.document.body.judges:
            self.document.metadata_fields.add(
                MetadataField(
                    name=self.key,
                    value=name,
                    source=MetadataSource.DOCUMENT,
                )
            )

    def add_editor_judge(self, name: str) -> None:
        """Add an EDITOR claim for a judge name, yanking body first if needed."""
        cleaned = name.strip()
        if not cleaned:
            return

        self.materialise_body_claims()
        self.document.metadata_fields.add(
            MetadataField(
                name=self.key,
                value=cleaned,
                source=MetadataSource.EDITOR,
            )
        )

    def suppress_claim(self, claim_id: str) -> None:
        """Suppress a judges claim: reject document/external, hard-remove editor."""
        self.materialise_body_claims()
        claim = self.document.metadata_fields[claim_id]
        if claim.name != self.key:
            raise KeyError(f"Claim {claim_id} is not a '{self.key}' claim")

        if claim.source is MetadataSource.EDITOR:
            self.document.metadata_fields.remove(claim_id)
        else:
            self.document.metadata_fields.reject(claim_id)

    def restore_claim(self, claim_id: str) -> None:
        """Restore a previously rejected judges claim."""
        claim = self.document.metadata_fields[claim_id]
        if claim.name != self.key:
            raise KeyError(f"Claim {claim_id} is not a '{self.key}' claim")
        if claim.source is MetadataSource.EDITOR:
            raise MetadataFieldRemovalNotAllowedException(
                f"Cannot restore editor claim {claim_id}; editor claims are hard-removed rather than rejected."
            )
        self.document.metadata_fields.restore(claim_id)

    def suppress_body_value(self, name: str) -> None:
        """Yank body claims if needed, then reject the DOCUMENT claim matching ``name``."""
        cleaned = name.strip()
        if not cleaned:
            return

        self.materialise_body_claims()
        for claim in self.document.metadata_fields.by_name(self.key):
            if claim.rejected:
                continue
            if claim.source is MetadataSource.DOCUMENT and claim.value == cleaned:
                self.document.metadata_fields.reject(claim.id)
                return
