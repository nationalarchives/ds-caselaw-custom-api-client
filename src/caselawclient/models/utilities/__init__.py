import re
from typing import TypedDict

from requests_toolbelt.multipart.decoder import BodyPart

from caselawclient.types import DocumentURIString, MarkLogicDocumentURIString

VERSION_REGEX = r"xml_versions/(\d{1,10})-"
# Here we limit the number of digits in the version to 10 on purpose, see
# https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS for an explanation of why.


class VersionsDict(TypedDict):
    uri: DocumentURIString
    version: int


def render_versions(decoded_versions: list[BodyPart]) -> list[VersionsDict]:
    versions: list[VersionsDict] = [
        {
            "uri": MarkLogicDocumentURIString(part.text).as_document_uri(),
            "version": extract_version(part.text),
        }
        for part in decoded_versions
    ]
    sorted_versions = sorted(versions, key=lambda d: -d["version"])
    return sorted_versions


def extract_version(version_string: str) -> int:
    result = re.search(VERSION_REGEX, version_string)
    return int(result.group(1)) if result else 0
