from src.caselawclient.content_hash import (
    content_hash,
    hashable_text,
    validate_content_hash,
)

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


def test_hashable_text_valid_doc():
    """
    Do we correctly identify the text to hash, omitting the meta section and removing spaces?
    Notably, the text from the meta section should NOT appear.
    """
    assert hashable_text(VALID_DOC) == b"Dousethisvalidtext"


def test_hashable_text_invalid_doc():
    assert hashable_text(INVALID_DOC) == b"Donotusethisinvalidtext"


def test_content_hash():
    """Do we get a hex string when hashing the document, and is it what we expect?"""
    assert (
        content_hash(VALID_DOC)
        == "c4367ebc0937f4dc2d6b372d9a09670e3606a5b3da77a070149755db5f942565"
    )
    assert (
        content_hash(INVALID_DOC)
        != "c4367ebc0937f4dc2d6b372d9a09670e3606a5b3da77a070149755db5f942565"
    )


def test_validate_content_hash():
    """Do valid documents pass, and invalid ones fail? i.e. check the hash in the document"""
    assert validate_content_hash(VALID_DOC)
    assert not validate_content_hash(INVALID_DOC)
