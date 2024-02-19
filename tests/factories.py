import datetime
from typing import Any
from unittest.mock import Mock

from typing_extensions import TypeAlias

from caselawclient.models.documents import Document
from caselawclient.models.judgments import Judgment
from caselawclient.responses.search_result import SearchResult, SearchResultMetadata


class DocumentFactory:
    # "name_of_attribute": ("name of incoming param", "default value")
    PARAMS_MAP: dict[str, tuple[str, Any]] = {
        "uri": ("uri", "test/2023/123"),
        "name": ("name", "Judgment v Judgement"),
        "neutral_citation": ("neutral_citation", "[2023] Test 123"),
        "best_human_identifier": ("neutral_citation", "[2023] Test 123"),
        "court": ("court", "Court of Testing"),
        "document_date_as_string": ("document_date_as_string", "2023-02-03"),
        "is_published": ("is_published", False),
        "is_sensitive": ("is_sensitive", False),
        "is_anonymised": ("is_anonymised", False),
        "has_supplementary_materials": ("has_supplementary_materials", False),
        "is_failure": ("is_failure", False),
        "source_name": ("source_name", "Example Uploader"),
        "source_email": ("source_email", "uploader@example.com"),
        "consignment_reference": ("consignment_reference", "TDR-12345"),
        "assigned_to": ("assigned_to", ""),
        "versions": ("versions", []),
        "document_noun": ("document_noun", "judgment"),
    }

    @classmethod
    def build(cls, **kwargs) -> Judgment:
        judgment_mock = Mock(spec=Judgment, autospec=True)

        if "html" in kwargs:
            judgment_mock.return_value.content_as_html.return_value = kwargs.pop("html")
        else:
            judgment_mock.return_value.content_as_html.return_value = (
                "<p>This is a judgment.</p>"
            )

        if "xml" in kwargs:
            xml_string = kwargs.pop("xml")
        else:
            xml_string = "<akomantoso>This is some XML of a judgment.</akomantoso>"

        judgment_mock.return_value.xml = Document.XML(
            xml_bytestring=xml_string.encode(encoding="utf-8")
        )

        for map_to, map_from in cls.PARAMS_MAP.items():
            if map_from[0] in kwargs:
                value = kwargs[map_from[0]]
            else:
                value = map_from[1]
            setattr(judgment_mock.return_value, map_to, value)

        return judgment_mock()


class SimpleFactory:
    # "name_of_attribute": ("name of incoming param", "default value")
    PARAMS_MAP: dict[str, Any]

    target_class: TypeAlias = object

    @classmethod
    def build(cls, **kwargs) -> target_class:
        mock_object = Mock(spec=cls.target_class, autospec=True)

        for param, default in cls.PARAMS_MAP.items():
            if param in kwargs:
                setattr(mock_object.return_value, param, kwargs[param])
            else:
                setattr(mock_object.return_value, param, default)

        return mock_object()


class SearchResultMetadataFactory(SimpleFactory):
    target_class = SearchResultMetadata
    # "name_of_attribute": ("name of incoming param", "default value")
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


class JudgmentFactory(DocumentFactory):
    pass


class PressSummaryFactory(DocumentFactory):
    pass
