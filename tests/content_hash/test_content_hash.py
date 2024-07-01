import pytest
from caselawclient.content_hash import (
    get_hash_from_document,
    get_hashable_text,
    validate_content_hash,
)
from caselawclient.errors import InvalidContentHashError

VALID_DOC = b"""<?xml version="1.0" encoding="UTF-8"?>
    <akomaNtoso
      xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
      xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
      <judgment name="judgment">
        <meta>
        <proprietary>
        <uk:hash>c4367ebc0937f4dc2d6b372d9a09670e3606a5b3da77a070149755db5f942565</uk:hash>
        <uk:cite>the meta section should not be present BAD</uk:cite>
        </proprietary>
        </meta>
        <p>Do <b>use</b></p>
        <p>this <i>valid</i> text</p>
      </judgment>
    </akomaNtoso>
    """

INVALID_DOC = VALID_DOC.replace(b"Do", b"Do not").replace(b"valid", b"invalid")

VALID_DOC_CONTENT_HASH = "c4367ebc0937f4dc2d6b372d9a09670e3606a5b3da77a070149755db5f942565"


class TestIdentifyHashableString:
    def test_hashable_text_valid_doc(self):
        """
        Do we correctly identify the text to hash, omitting the meta section and removing spaces?
        Notably, the text from the meta section should NOT appear.
        """
        assert get_hashable_text(VALID_DOC) == b"Dousethisvalidtext"

    def test_hashable_text_invalid_doc(self):
        assert get_hashable_text(INVALID_DOC) == b"Donotusethisinvalidtext"


class TestCorrectHashForString:
    def test_valid_content_hash(self):
        """Do we get a hex string when hashing the document, and is it what we expect?"""
        assert get_hash_from_document(VALID_DOC) == VALID_DOC_CONTENT_HASH

    def test_invalid_content_hash(self):
        assert get_hash_from_document(INVALID_DOC) != VALID_DOC_CONTENT_HASH


class TestCorrectlyRaisesExceptions:
    def test_valid_content_hash(self):
        """Do valid documents pass, and invalid ones fail? i.e. check the hash in the document"""
        assert validate_content_hash(VALID_DOC) == VALID_DOC_CONTENT_HASH

    def test_wrong_content_hash(self):
        with pytest.raises(
            InvalidContentHashError,
            match=f'Hash of existing tag is "{VALID_DOC_CONTENT_HASH}',
        ):
            validate_content_hash(INVALID_DOC)

    def test_no_content_hash(self):
        with pytest.raises(
            InvalidContentHashError,
            match="Document did not have a content hash tag",
        ):
            validate_content_hash(b"<dog></dog>")
