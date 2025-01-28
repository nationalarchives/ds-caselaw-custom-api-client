from caselawclient.identifier_resolution import IdentifierResolutions
from caselawclient.models.identifiers.neutral_citation import NeutralCitationNumber

raw_marklogic_resolutions = [
    """
                                 {"documents.compiled_url_slugs.identifier_uuid":"24b9a384-8bcf-4f20-996a-5c318f8dc657",
                                  "documents.compiled_url_slugs.document_uri":"/ewca/civ/2003/547.xml",
                                  "documents.compiled_url_slugs.identifier_slug":"ewca/civ/2003/54721",
                                  "documents.compiled_url_slugs.document_published":"false",
                                  "documents.compiled_url_slugs.identifier_namespace":"ukncn",
                                  "documents.compiled_url_slugs.identifier_value":"[2003] EWCA 54721 (Civ)"
                                  }
                                 """,
    """
                                 {"documents.compiled_url_slugs.identifier_uuid":"x",
                                  "documents.compiled_url_slugs.document_uri":"x",
                                  "documents.compiled_url_slugs.identifier_slug":"x",
                                  "documents.compiled_url_slugs.document_published":"true",
                                  "documents.compiled_url_slugs.identifier_namespace":"ukncn",
                                  "documents.compiled_url_slugs.identifier_value":"X"
                                  }
                                 """,
]


def test_decoded_identifier():
    decoded_resolutions = IdentifierResolutions.from_marklogic_output(raw_marklogic_resolutions)
    res = decoded_resolutions[0]
    assert res.identifier_uuid == "24b9a384-8bcf-4f20-996a-5c318f8dc657"
    assert res.document_uri == "/ewca/civ/2003/547.xml"
    assert res.identifier_slug == "ewca/civ/2003/54721"
    assert res.identifier_namespace == "ukncn"
    assert res.identifier_type == NeutralCitationNumber
    assert res.identifier_value == "[2003] EWCA 54721 (Civ)"
    assert res.document_published == False  # noqa: E712


def test_published():
    decoded_resolutions = IdentifierResolutions.from_marklogic_output(raw_marklogic_resolutions)
    assert len(decoded_resolutions.published()) == 1
    assert decoded_resolutions.published()[0] == decoded_resolutions[1]
