import lxml.etree

from caselawclient.models.documents.stub import EditorStubData, create_stub

NAMESPACES = {
    "uk": "https://caselaw.nationalarchives.gov.uk/akn",
    "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
}


def xpath(root, xpath):
    return lxml.etree.tostring(root.xpath(xpath, namespaces=NAMESPACES)[0])


def test_create_stub():
    data: EditorStubData = EditorStubData(
        decision_date="2025-01-01",
        transform_datetime="2025-01-01T00:00:00",
        court_code_upper="UKFTT-GRC",
        title="Test Case",
        year="2025",
        case_numbers=["AB-12345", "CD-67890"],
        parties=[{"role": "Claimant", "name": "Jerry"}, {"role": "Defendant", "name": "Tom"}],
    )

    stub = lxml.etree.tostring(lxml.etree.fromstring(create_stub(data)))
    assert b"xml" in stub
    assert b'<FRBRname value="Test Case"/>' in stub
    assert b'<FRBRdate date="2025-01-01" name="decision"/>' in stub
    assert b'<FRBRauthor href="#ukftt-grc"/>' in stub
    assert (
        b'<TLCOrganization eId="ukftt-grc" href="https://www.gov.uk/courts-tribunals/first-tier-tribunal-general-regulatory-chamber" showAs="United Kingdom First-tier Tribunal (General Regulatory Chamber)"/>'
        in stub
    )
    assert b"<uk:court>UKFTT-GRC</uk:court>" in stub
    assert b"<uk:year>2025</uk:year>" in stub
    assert b'<uk:party role="Claimant">Jerry</uk:party>' in stub
    assert b'<uk:party role="Defendant">Tom</uk:party>' in stub
    assert b"<uk:parser" not in stub  # TODO: fix this
    assert b'<FRBRdate date="2025-01-01T00:00:00" name="transform"/>' in stub
    assert b"<uk:caseNumber>AB-12345</uk:caseNumber>" in stub
    assert b"<uk:caseNumber>CD-67890</uk:caseNumber>" in stub
