from caselawclient.models.documents.metadata.base import SingleMetadata


class CourtMetadata(SingleMetadata[str]):
    key = "court"
    title = "Court"
    description = "The court that issued the document."

    @property
    def value(self) -> str:
        return self.document.body.court
