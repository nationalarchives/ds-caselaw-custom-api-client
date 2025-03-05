import importlib
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional

from ds_caselaw_utils.types import NeutralCitationString

from caselawclient.errors import DocumentNotFoundError
from caselawclient.identifier_resolution import IdentifierResolutions
from caselawclient.models.neutral_citation_mixin import NeutralCitationMixin

if TYPE_CHECKING:
    from caselawclient.models.press_summaries import PressSummary

from caselawclient.types import DocumentURIString

from .documents import Document


class Judgment(NeutralCitationMixin, Document):
    """
    Represents a judgment document.
    """

    document_noun = "judgment"
    document_noun_plural = "judgments"
    type_collection_name = "judgment"

    def __init__(self, uri: DocumentURIString, *args: Any, **kwargs: Any) -> None:
        super().__init__(self.document_noun, uri, *args, **kwargs)

    @cached_property
    def neutral_citation(self) -> Optional[NeutralCitationString]:
        value_in_xml = self.body.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:cite/text()",
            {
                "uk": "https://caselaw.nationalarchives.gov.uk/akn",
                "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
            },
        )
        if value_in_xml:
            return NeutralCitationString(value_in_xml)
        return None

    @cached_property
    def linked_document(self) -> Optional["PressSummary"]:
        """
        Attempt to fetch a linked press summary, and return it, if it exists
        """
        try:
            uri = DocumentURIString(self.uri + "/press-summary/1")
            if not TYPE_CHECKING:  # This isn't nice, but will be cleaned up when we refactor how related documents work
                PressSummary = importlib.import_module("caselawclient.models.press_summaries").PressSummary
            return PressSummary(uri, self.api_client)
        except DocumentNotFoundError:
            return None

    @cached_property
    def linked_press_summaries(self, only_published: bool = True) -> "IdentifierResolutions":
        return self.linked_document_resolutions(["uksummaryofncn"], only_published)
