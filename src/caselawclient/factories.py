import datetime
from typing import Any, cast
from unittest.mock import Mock, patch

from typing_extensions import TypeAlias

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.documents import Document
from caselawclient.models.documents.body import DocumentBody
from caselawclient.models.judgments import Judgment
from caselawclient.models.press_summaries import PressSummary
from caselawclient.responses.search_result import SearchResult, SearchResultMetadata


class DocumentBodyFactory:
    # "name_of_attribute": "default value"
    PARAMS_MAP: dict[str, Any] = {
        "name": "Judgment v Judgement",
        "court": "Court of Testing",
        "document_date_as_string": "2023-02-03",
    }

    @classmethod
    def build(cls, **kwargs: Any) -> DocumentBody:
        xml_string = (
            kwargs.pop("xml") if "xml" in kwargs else "<akomantoso>This is some XML of a judgment.</akomantoso>"
        )

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
    def build(cls, uri: str = "test/2023/123", **kwargs: Any) -> target_class:
        if "api_client" in kwargs:
            mock_api_client = kwargs.pop("api_client")
        else:
            mock_api_client = Mock(spec=MarklogicApiClient)
            mock_api_client.get_judgment_xml_bytestring.return_value = (
                b"<akomantoso>This is some XML of a judgment.</akomantoso>"
            )

        html_patched_return = kwargs.pop("html") if "html" in kwargs else "<p>This is a judgment.</p>"

        with patch.object(cls.target_class, "content_as_html") as mock_content_as_html:
            mock_content_as_html.return_value = html_patched_return
            document = cls.target_class(uri, api_client=mock_api_client)

        document.body = kwargs.pop("body") if "body" in kwargs else DocumentBodyFactory.build()

        for param_name, default_value in cls.PARAMS_MAP.items():
            value = kwargs.get(param_name, default_value)
            setattr(document, param_name, value)

        return document


class JudgmentFactory(DocumentFactory):
    target_class = Judgment

    def __init__(self) -> None:
        self.PARAMS_MAP = self.PARAMS_MAP | {
            "neutral_citation": "[2023] Test 123",
            "best_human_identifier": "[2023] Test 123",
        }

        super().__init__()

    @classmethod
    def build(cls, uri: str = "test/2023/123", **kwargs: Any) -> Judgment:
        return cast(Judgment, super().build(uri, **kwargs))


class PressSummaryFactory(DocumentFactory):
    target_class = PressSummary

    def __init__(self) -> None:
        self.PARAMS_MAP = self.PARAMS_MAP | {
            "neutral_citation": "[2023] Test 123",
            "best_human_identifier": "[2023] Test 123",
        }

        super().__init__()

    @classmethod
    def build(cls, uri: str = "test/2023/123/press-summary/1", **kwargs: Any) -> PressSummary:
        return cast(PressSummary, super().build(uri, **kwargs))


class SimpleFactory:
    # "name_of_attribute": "default value"
    PARAMS_MAP: dict[str, Any]

    target_class: TypeAlias = object

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
    }


class SearchResultFactory(SimpleFactory):
    target_class = SearchResult

    # "name_of_attribute": ("name of incoming param", "default value")
    PARAMS_MAP = {
        "uri": "test/2023/123",
        "name": "Judgment v Judgement",
        "neutral_citation": "[2023] Test 123",
        "court": "Court of Testing",
        "date": datetime.date(2023, 2, 3),
        "metadata": SearchResultMetadataFactory.build(),
        "is_failure": False,
    }
