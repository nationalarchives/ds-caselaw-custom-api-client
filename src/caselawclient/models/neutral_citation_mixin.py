from functools import cached_property
from typing import Any

from ds_caselaw_utils import neutral_url


class NeutralCitationMixin:
    """
    A mixin class that provides functionality related to neutral citation.

    The NeutralCitationMixin is intended to be used as a mixin in classes that represent legal documents
    and need to handle neutral citation attributes and validation.

    Notes:
        - The document_noun attribute should be set in the child class that uses this mixin to provide
          context-specific document noun strings for error messages and validation checks.
        - The neutral_citation() method must be implemented in the child class to return the actual
          neutral citation string for the legal document.
    """

    def __init__(self, document_noun: str, *args: Any, **kwargs: Any) -> None:
        self.attributes_to_validate: list[
            tuple[str, bool, str]
        ] = self.attributes_to_validate + [
            (
                "has_ncn",
                True,
                f"This {document_noun} has no neutral citation number",
            ),
            (
                "has_valid_ncn",
                True,
                f"The neutral citation number of this {document_noun} is not valid",
            ),
        ]

        super(NeutralCitationMixin, self).__init__(*args, **kwargs)

    @cached_property
    def neutral_citation(self) -> str:
        return ""

    @cached_property
    def has_ncn(self) -> bool:
        if not self.neutral_citation:
            return False

        return True

    @cached_property
    def has_valid_ncn(self) -> bool:
        if not self.has_ncn or not neutral_url(self.neutral_citation):
            return False

        return True
