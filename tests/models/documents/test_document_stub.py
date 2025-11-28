from caselawclient.models.documents.stub import StubData, create_stub


def test_create_stub():
    data: StubData = StubData(
        decision_date="2025-01-01",
        transform_datetime="2025-01-01T00:00:00",
        court_code_upper="UKFTT-GRC",
        court_code_lower="ukftt-grc",
        title="Test Case",
        court_url="https://example.com/court",
        court_full_name="Example Court",
        year="2025",
        case_number=["AB-12345", "CD-67890"],
        parties=[{"role": "Claimant", "name": "Jerry"}, {"role": "Defendant", "name": "Tom"}],
    )

    stub = create_stub(data)
    assert b"xml" in stub
    assert b'<FRBRname value="Test Case" />' in stub
    assert b"Jerry" in stub
    assert b"Tom" in stub
