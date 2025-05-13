import datetime
import json
from typing import Any, Optional
from unittest.mock import Mock

from typing_extensions import TypeAlias

from caselawclient.Client import MarklogicApiClient
from caselawclient.identifier_resolution import IdentifierResolution, IdentifierResolutions
from caselawclient.models.documents import Document
from caselawclient.models.documents.body import DocumentBody
from caselawclient.models.identifiers import Identifier
from caselawclient.models.identifiers.fclid import FindCaseLawIdentifier
from caselawclient.models.judgments import Judgment
from caselawclient.models.press_summaries import PressSummary
from caselawclient.responses.search_result import SearchResult, SearchResultMetadata
from caselawclient.types import DocumentURIString

DEFAULT_DOCUMENT_BODY_XML = """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
            <judgment name="decision">
                <meta/><header/>
                <judgmentBody>
                <decision>
                <p>This is a document.</p>
                </decision>
                </judgmentBody>
            </judgment>
            </akomaNtoso>"""


class DocumentBodyFactory:
    # "name_of_attribute": "default value"
    PARAMS_MAP: dict[str, Any] = {
        "name": "Judgment v Judgement",
        "court": "Court of Testing",
        "document_date_as_string": "2023-02-03",
    }

    @classmethod
    def build(cls, xml_string: str = DEFAULT_DOCUMENT_BODY_XML, **kwargs: Any) -> DocumentBody:
        document_body = DocumentBody(
            xml_bytestring=xml_string.encode(encoding="utf-8"),
        )

        for param_name, default_value in cls.PARAMS_MAP.items():
            value = kwargs.get(param_name, default_value)
            setattr(document_body, param_name, value)

        return document_body


class DocumentFactory:
    # "name_of_attribute": "default value"
    PARAMS_MAP: dict[str, Any] = {
        "is_published": False,
        "is_sensitive": False,
        "is_anonymised": False,
        "is_failure": False,
        "source_name": "Example Uploader",
        "source_email": "uploader@example.com",
        "consignment_reference": "TDR-12345",
        "assigned_to": "",
        "versions": [],
    }

    target_class: TypeAlias = Document

    @classmethod
    def build(
        cls,
        uri: DocumentURIString = DocumentURIString("test/2023/123"),
        api_client: Optional[MarklogicApiClient] = None,
        identifiers: Optional[list[Identifier]] = None,
        **kwargs: Any,
    ) -> target_class:
        def _fake_linked_documents(*args: Any, **kwargs: Any) -> list["Document"]:
            return [document]

        if not api_client:
            api_client = Mock(spec=MarklogicApiClient)
            api_client.get_judgment_xml_bytestring.return_value = DEFAULT_DOCUMENT_BODY_XML.encode(encoding="utf-8")
            api_client.get_property_as_node.return_value = None

        document = cls.target_class(uri, api_client=api_client)
        document.body = kwargs.pop("body") if "body" in kwargs else DocumentBodyFactory.build()

        if identifiers is None:
            document.identifiers.add(FindCaseLawIdentifier(value="tn4t35ts"))
        else:
            for identifier in identifiers:
                document.identifiers.add(identifier)

        setattr(document, "linked_documents", _fake_linked_documents)

        for param_name, default_value in cls.PARAMS_MAP.items():
            value = kwargs.get(param_name, default_value)
            setattr(document, param_name, value)

        return document


class JudgmentFactory(DocumentFactory):
    target_class: TypeAlias = Judgment
    PARAMS_MAP = DocumentFactory.PARAMS_MAP | {
        "neutral_citation": "[2023] Test 123",
    }


class PressSummaryFactory(DocumentFactory):
    target_class: TypeAlias = PressSummary
    PARAMS_MAP = DocumentFactory.PARAMS_MAP | {
        "neutral_citation": "[2023] Test 123",
    }


class SimpleFactory:
    target_class: TypeAlias = object
    # "name_of_attribute": "default value"
    PARAMS_MAP: dict[str, Any]

    @classmethod
    def build(cls, **kwargs: Any) -> target_class:
        mock_object = Mock(spec=cls.target_class, autospec=True)

        for param, default in cls.PARAMS_MAP.items():
            if param in kwargs:
                setattr(mock_object.return_value, param, kwargs[param])
            else:
                setattr(mock_object.return_value, param, default)

        return mock_object()


class SearchResultMetadataFactory(SimpleFactory):
    target_class = SearchResultMetadata
    # "name_of_attribute": "default value"
    PARAMS_MAP = {
        "author": "Fake Name",
        "author_email": "fake.email@gov.invalid",
        "consignment_reference": "TDR-2023-ABC",
        "submission_datetime": datetime.datetime(2023, 2, 3, 9, 12, 34),
        "editor_status": "New",
    }


class SearchResultFactory(SimpleFactory):
    target_class = SearchResult

    PARAMS_MAP = {
        "uri": "d-a1b2c3",
        "name": "Judgment v Judgement",
        "neutral_citation": "[2025] UKSC 123",
        "court": "Court of Testing",
        "date": datetime.datetime(2023, 2, 3),
        "transformation_date": datetime.datetime(2023, 2, 3, 12, 34).isoformat(),
        "metadata": SearchResultMetadataFactory.build(),
        "is_failure": False,
        "matches": None,
        "slug": "uksc/2025/1",
        "content_hash": "ed7002b439e9ac845f22357d822bac1444730fbdb6016d3ec9432297b9ec9f73",
    }


class IdentifierResolutionFactory:
    @classmethod
    def build(
        self,
        resolution_uuid: Optional[str] = None,
        document_uri: Optional[str] = None,
        identifier_slug: Optional[str] = None,
        published: Optional[bool] = True,
        namespace: Optional[str] = None,
        value: Optional[str] = None,
    ) -> IdentifierResolution:
        raw_resolution = {
            "documents.compiled_url_slugs.identifier_uuid": resolution_uuid or "24b9a384-8bcf-4f20-996a-5c318f8dc657",
            "documents.compiled_url_slugs.document_uri": document_uri or "/ewca/civ/2003/547.xml",
            "documents.compiled_url_slugs.identifier_slug": identifier_slug or "ewca/civ/2003/54721",
            "documents.compiled_url_slugs.document_published": published,
            "documents.compiled_url_slugs.identifier_namespace": namespace or "ukncn",
            "documents.compiled_url_slugs.identifier_value": value or "[2003] EWCA 54721 (Civ)",
        }
        return IdentifierResolution.from_marklogic_output(json.dumps(raw_resolution))


class IdentifierResolutionsFactory:
    @classmethod
    def build(self, resolutions: Optional[list[IdentifierResolution]] = None) -> IdentifierResolutions:
        if resolutions is None:
            resolutions = [IdentifierResolutionFactory.build()]
        return IdentifierResolutions(resolutions)
