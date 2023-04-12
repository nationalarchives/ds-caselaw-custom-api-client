import re
import xml.etree.ElementTree as ET

VERSION_REGEX = r"xml_versions/(\d{1,10})-(\d{1,10}|TDR)"
# Here we limit the number of digits in the version and document reference to 10 on purpose, see
# https://owasp.org/www-community/attacks/Regular_expression_Denial_of_Service_-_ReDoS for an explanation of why.

akn_namespace = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
uk_namespace = {"uk": "https://caselaw.nationalarchives.gov.uk/akn"}


def get_judgment_root(judgment_xml) -> str:
    try:
        parsed_xml = ET.XML(bytes(judgment_xml, encoding="utf-8"))
        return parsed_xml.tag
    except ET.ParseError:
        return "error"


def render_versions(decoded_versions):
    versions = [
        {
            "uri": part.text.rstrip(".xml"),
            "version": extract_version(part.text),
        }
        for part in decoded_versions
    ]
    sorted_versions = sorted(versions, key=lambda d: -d["version"])
    return sorted_versions


def extract_version(version_string: str) -> int:
    result = re.search(VERSION_REGEX, version_string)
    return int(result.group(1)) if result else 0
