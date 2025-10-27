from pytest import raises

from caselawclient.types import (
    DocumentURIString,
    FailureTuple,
    InvalidDocumentURIException,
    InvalidMarkLogicDocumentURIException,
    MarkLogicDocumentURIString,
    SuccessTuple,
)


class TestMarkLogicDocumentURIString:
    def test_must_begin_with_slash(self):
        with raises(
            InvalidMarkLogicDocumentURIException,
            match='"test/2025/123.xml" is not a valid MarkLogic document URI; URIs must begin with a slash.',
        ):
            MarkLogicDocumentURIString("test/2025/123.xml")

    def test_must_end_with_dotxml(self):
        with raises(
            InvalidMarkLogicDocumentURIException,
            match='"/test/2025/123" is not a valid MarkLogic document URI; URIs must end with ".xml".',
        ):
            MarkLogicDocumentURIString("/test/2025/123")

    def test_as_documenturi(self):
        marklogic_uri = MarkLogicDocumentURIString("/test/2025/123.xml")

        document_uri = marklogic_uri.as_document_uri()

        assert document_uri == "test/2025/123"
        assert type(document_uri) is DocumentURIString


class TestDocumentURIString:
    def test_must_not_begin_with_slash(self):
        with raises(
            InvalidDocumentURIException,
            match='"/test/2025/123" is not a valid document URI; URIs cannot begin or end with slashes.',
        ):
            DocumentURIString("/test/2025/123")

    def test_must_not_end_with_slash(self):
        with raises(
            InvalidDocumentURIException,
            match='"test/2025/123/" is not a valid document URI; URIs cannot begin or end with slashes.',
        ):
            DocumentURIString("test/2025/123/")

    def test_must_not_contain_dot(self):
        with raises(
            InvalidDocumentURIException,
            match='"test/2025/123.456" is not a valid document URI; URIs cannot contain full stops.',
        ):
            DocumentURIString("test/2025/123.456")

    def test_as_marklogic(self):
        document_uri = DocumentURIString("test/2025/123")

        marklogic_uri = document_uri.as_marklogic()

        assert marklogic_uri == "/test/2025/123.xml"
        assert type(marklogic_uri) is MarkLogicDocumentURIString


class TestSuccessFailureMessageTuple:
    def test_or(self):
        assert SuccessTuple() | SuccessTuple() == SuccessTuple()
        assert SuccessTuple() | FailureTuple("cow") == FailureTuple("cow")
        assert FailureTuple("cow") | FailureTuple(["bat", "ant"]) == FailureTuple(["cow", "bat", "ant"])

    def test_bool(self):
        assert SuccessTuple()
        assert not FailureTuple("")

        assert SuccessTuple().success
        assert not FailureTuple("").success

        assert SuccessTuple()[0]
        assert not FailureTuple("")[0]

    def test_repr(self):
        assert repr(FailureTuple("cow")) == "SuccessFailureMessageTuple(False, ['cow'])"
