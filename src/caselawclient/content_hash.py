"""
The content hash is the SHA256 hash of the judgment text with all whitespace removed.
This is intended to confirm that various processing has not changed the content of
the judgment, whilst allowing variations in the XML which might not allow for
preservation of whitespace.

The canonical version of this hashing function is in the parser:
https://github.com/nationalarchives/tna-judgments-parser/blob/main/src/akn/SHA256.cs
"""

import re
from hashlib import sha256

import lxml.etree

from .errors import InvalidContentHashError


def hash_of_content(doc: bytes) -> str:
    """Return the content hash for a document"""
    return sha256(hashable_text(doc)).hexdigest()


def hashable_text(doc: bytes) -> bytes:
    """Extract the text (as UTF-8 bytes) that would be hashed"""
    root = lxml.etree.fromstring(doc)
    metadatas = root.xpath(
        "//akn:meta",
        namespaces={"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"},
    )
    for (
        metadata
    ) in metadatas:  # there should be no more than one, but handle zero case gracefully
        metadata.getparent().remove(metadata)
    text = "".join(root.itertext())
    spaceless = re.sub(r"\s", "", text)
    return spaceless.encode("utf-8")


def validate_content_hash(doc: bytes) -> str:
    """Check a document's self-described content hash is the same as the hash of its content, raise an error if not"""
    root = lxml.etree.fromstring(doc)
    try:
        hash_from_tag = root.xpath(
            "//uk:hash/text()",
            namespaces={"uk": "https://caselaw.nationalarchives.gov.uk/akn"},
        )[0]
    except IndexError:
        raise InvalidContentHashError("Document did not have a content hash tag")
    content_hash = hash_of_content(doc)
    if hash_from_tag != content_hash:
        raise InvalidContentHashError(
            f"Hash of document was {hash_from_tag} but the content hash was {content_hash}"
        )
    return content_hash
