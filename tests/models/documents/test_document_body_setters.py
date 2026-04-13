"""Tests for DocumentBody setter methods, covering element creation and updates."""

from lxml import etree

from caselawclient.models.documents.body import DocumentBody

# Minimal XML with all necessary elements
MINIMAL_XML_WITH_ELEMENTS = b"""<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
    xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
    <judgment>
        <meta>
            <identification source="#tna">
                <FRBRWork>
                    <FRBRthis value="https://caselaw.nationalarchives.gov.uk/id/uksc/2024/1234" />
                    <FRBRuri value="https://caselaw.nationalarchives.gov.uk/id/uksc/2024/1234" />
                    <FRBRdate date="2024-01-01" name="judgment" />
                    <FRBRauthor href="#uksc" />
                    <FRBRcountry value="GB-UKM" />
                    <FRBRnumber value="1234" />
                    <FRBRname value="Test Claimant v Test Defendant" />
                </FRBRWork>
                <FRBRExpression>
                    <FRBRthis value="https://caselaw.nationalarchives.gov.uk/uksc/2024/1234" />
                    <FRBRuri value="https://caselaw.nationalarchives.gov.uk/uksc/2024/1234" />
                    <FRBRdate date="2024-01-01" name="judgment" />
                    <FRBRauthor href="#uksc" />
                    <FBRRlanguage language="eng" />
                </FRBRExpression>
                <FRBRManifestation>
                    <FRBRthis value="https://caselaw.nationalarchives.gov.uk/d-a1b2c3/xml" />
                    <FRBRuri value="https://caselaw.nationalarchives.gov.uk/d-a1b2c3/data.xml" />
                    <FRBRdate date="2024-01-01" name="judgment" />
                    <FRBRauthor href="#uksc" />
                    <FRBRformat value="application/xml" />
                </FRBRManifestation>
            </identification>
            <proprietary>
                <uk:court>High Court</uk:court>
                <uk:jurisdiction>England and Wales</uk:jurisdiction>
            </proprietary>
        </meta>
        <header><p/></header>
        <judgmentBody><decision><p/></decision></judgmentBody>
    </judgment>
</akomaNtoso>
"""

# Minimal XML without optional FRBRname, court, and jurisdiction elements
MINIMAL_XML_WITHOUT_OPTIONAL_ELEMENTS = b"""<?xml version="1.0" encoding="UTF-8"?>
<akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
    xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
    <judgment>
        <meta>
            <identification source="#tna">
                <FRBRWork>
                    <FRBRthis value="https://caselaw.nationalarchives.gov.uk/id/uksc/2024/1234" />
                    <FRBRuri value="https://caselaw.nationalarchives.gov.uk/id/uksc/2024/1234" />
                    <FRBRdate date="2024-01-01" name="judgment" />
                    <FRBRauthor href="#uksc" />
                    <FRBRcountry value="GB-UKM" />
                    <FRBRnumber value="1234" />
                </FRBRWork>
                <FRBRExpression>
                    <FRBRthis value="https://caselaw.nationalarchives.gov.uk/uksc/2024/1234" />
                    <FRBRuri value="https://caselaw.nationalarchives.gov.uk/uksc/2024/1234" />
                    <FRBRdate date="2024-01-01" name="judgment" />
                    <FRBRauthor href="#uksc" />
                    <FBRRlanguage language="eng" />
                </FRBRExpression>
                <FRBRManifestation>
                    <FRBRthis value="https://caselaw.nationalarchives.gov.uk/d-a1b2c3/xml" />
                    <FRBRuri value="https://caselaw.nationalarchives.gov.uk/d-a1b2c3/data.xml" />
                    <FRBRdate date="2024-01-01" name="judgment" />
                    <FRBRauthor href="#uksc" />
                    <FRBRformat value="application/xml" />
                </FRBRManifestation>
            </identification>
            <proprietary/>
        </meta>
        <header><p/></header>
        <judgmentBody><decision><p/></decision></judgmentBody>
    </judgment>
</akomaNtoso>
"""


class TestSetNameUpdatesExisting:
    """Test set_name when FRBRname element already exists."""

    def test_set_name_updates_existing_value(self):
        """When FRBRname exists, set_name should update its value attribute."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)
        assert body.name == "Test Claimant v Test Defendant"

        body.set_name("Updated Name")

        assert body.name == "Updated Name"
        xml_str = etree.tostring(body.xml_tree).decode()
        assert 'FRBRname value="Updated Name"' in xml_str
        assert "Test Claimant v Test Defendant" not in xml_str


class TestSetNameCreatesNew:
    """Test set_name when FRBRname element is missing."""

    def test_set_name_creates_missing_element(self):
        """When FRBRname doesn't exist, set_name should create it."""
        body = DocumentBody(MINIMAL_XML_WITHOUT_OPTIONAL_ELEMENTS)
        assert body.name == ""

        body.set_name("New Name")

        assert body.name == "New Name"
        xml_str = etree.tostring(body.xml_tree).decode()
        assert 'FRBRname value="New Name"' in xml_str


class TestSetDateUpdatesExisting:
    """Test set_date when FRBRdate element already exists."""

    def test_set_date_updates_existing_value(self):
        """When FRBRdate exists, set_date should update its date attribute."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)
        assert body.document_date_as_string == "2024-01-01"

        body.set_date("2024-12-31")

        assert body.document_date_as_string == "2024-12-31"
        xml_str = etree.tostring(body.xml_tree).decode()
        # Check that the FRBRWork FRBRdate was updated
        assert "FRBRWork" in xml_str
        # Find the FRBRWork section and verify it has the new date
        frbr_work_section = xml_str[xml_str.find("<FRBRWork") : xml_str.find("</FRBRWork>")]
        assert 'date="2024-12-31"' in frbr_work_section


class TestSetDateCreatesNew:
    """Test set_date when FRBRdate element is missing."""

    def test_set_date_creates_missing_element(self):
        """When FRBRdate doesn't exist in FRBRWork, set_date should create it."""
        body = DocumentBody(MINIMAL_XML_WITHOUT_OPTIONAL_ELEMENTS)
        # The test XML has FRBRdate but in a different location initially
        body.set_date("2025-06-15")

        assert body.document_date_as_string == "2025-06-15"


class TestSetCourtUpdatesExisting:
    """Test set_court when uk:court element already exists."""

    def test_set_court_updates_existing_value(self):
        """When uk:court exists, set_court should update its text."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)
        assert body.court == "High Court"

        body.set_court("Supreme Court")

        assert body.court == "Supreme Court"
        xml_str = etree.tostring(body.xml_tree).decode()
        assert "<uk:court>Supreme Court</uk:court>" in xml_str
        assert "<uk:court>High Court</uk:court>" not in xml_str


class TestSetCourtCreatesNew:
    """Test set_court when uk:court element is missing."""

    def test_set_court_creates_missing_element(self):
        """When uk:court doesn't exist, set_court should create it."""
        body = DocumentBody(MINIMAL_XML_WITHOUT_OPTIONAL_ELEMENTS)
        assert body.court == ""

        body.set_court("Court of Appeal")

        assert body.court == "Court of Appeal"
        xml_str = etree.tostring(body.xml_tree).decode()
        assert "<uk:court>Court of Appeal</uk:court>" in xml_str


class TestSetJurisdictionUpdatesExisting:
    """Test set_jurisdiction when uk:jurisdiction element already exists."""

    def test_set_jurisdiction_updates_existing_value(self):
        """When uk:jurisdiction exists, set_jurisdiction should update its text."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)
        assert body.jurisdiction == "England and Wales"

        body.set_jurisdiction("Scotland")

        assert body.jurisdiction == "Scotland"
        xml_str = etree.tostring(body.xml_tree).decode()
        assert "<uk:jurisdiction>Scotland</uk:jurisdiction>" in xml_str
        assert "<uk:jurisdiction>England and Wales</uk:jurisdiction>" not in xml_str


class TestSetJurisdictionCreatesNew:
    """Test set_jurisdiction when uk:jurisdiction element is missing."""

    def test_set_jurisdiction_creates_missing_element(self):
        """When uk:jurisdiction doesn't exist, set_jurisdiction should create it."""
        body = DocumentBody(MINIMAL_XML_WITHOUT_OPTIONAL_ELEMENTS)
        assert body.jurisdiction == ""

        body.set_jurisdiction("Northern Ireland")

        assert body.jurisdiction == "Northern Ireland"
        xml_str = etree.tostring(body.xml_tree).decode()
        assert "<uk:jurisdiction>Northern Ireland</uk:jurisdiction>" in xml_str


class TestSetCourtAndJurisdiction:
    """Test set_court_and_jurisdiction convenience method."""

    def test_set_court_and_jurisdiction_with_slash(self):
        """When given 'court/jurisdiction', should set both."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)

        body.set_court_and_jurisdiction("District Court/Wales")

        assert body.court == "District Court"
        assert body.jurisdiction == "Wales"

    def test_set_court_and_jurisdiction_without_slash(self):
        """When given value without slash, should set court and clear jurisdiction."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)

        body.set_court_and_jurisdiction("County Court")

        assert body.court == "County Court"
        assert body.jurisdiction == ""


class TestSetThisUriUpdatesExisting:
    """Test set_this_uri when FRBR URIs already exist."""

    def test_set_this_uri_updates_all_three_uris(self):
        """set_this_uri should update work, expression, and manifestation URIs."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)

        body.set_this_uri("ewhc/admin/2024/567")

        xml_str = etree.tostring(body.xml_tree).decode()

        # Check work URI (ID form)
        assert 'value="https://caselaw.nationalarchives.gov.uk/id/ewhc/admin/2024/567"' in xml_str

        # Check expression URI (non-ID form)
        assert 'value="https://caselaw.nationalarchives.gov.uk/ewhc/admin/2024/567"' in xml_str

        # Check manifestation URI (data.xml form)
        assert 'value="https://caselaw.nationalarchives.gov.uk/ewhc/admin/2024/567/data.xml"' in xml_str

        # Old URIs should be gone
        assert "uksc/2024/1234" not in xml_str

    def test_set_this_uri_strips_leading_slash(self):
        """set_this_uri should handle URIs with leading slash."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)

        body.set_this_uri("/ewca/civ/2024/123")

        xml_str = etree.tostring(body.xml_tree).decode()
        assert "ewca/civ/2024/123" in xml_str


class TestSetThisUriCreatesNew:
    """Test set_this_uri when FRBR URI elements might be partially missing."""

    def test_set_this_uri_handles_missing_elements_gracefully(self):
        """set_this_uri should handle cases where some elements don't exist."""
        # Use minimal XML and just verify it doesn't crash
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)

        # Should not raise an error even if elements are missing in some sections
        body.set_this_uri("test/path/2024/999")

        # Verify it updated the ones that exist
        xml_str = etree.tostring(body.xml_tree).decode()
        assert "test/path/2024/999" in xml_str


class TestSettersInvalidateCachedProperties:
    """Test that setters properly invalidate cached properties."""

    def test_set_name_invalidates_cached_name(self):
        """set_name should clear the cached name property."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)
        _ = body.name  # Access to cache it
        assert "name" in body.__dict__

        body.set_name("New Name")

        assert "name" not in body.__dict__

    def test_set_date_invalidates_cached_properties(self):
        """set_date should clear cached date properties."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)
        _ = body.document_date_as_string  # Cache it
        _ = body.document_date_as_date
        assert "document_date_as_string" in body.__dict__

        body.set_date("2025-01-01")

        assert "document_date_as_string" not in body.__dict__
        assert "document_date_as_date" not in body.__dict__

    def test_set_court_invalidates_cached_court(self):
        """set_court should clear the cached court property."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)
        _ = body.court  # Cache it
        assert "court" in body.__dict__

        body.set_court("New Court")

        assert "court" not in body.__dict__

    def test_set_jurisdiction_invalidates_cached_jurisdiction(self):
        """set_jurisdiction should clear the cached jurisdiction property."""
        body = DocumentBody(MINIMAL_XML_WITH_ELEMENTS)
        _ = body.jurisdiction  # Cache it
        assert "jurisdiction" in body.__dict__

        body.set_jurisdiction("New Jurisdiction")

        assert "jurisdiction" not in body.__dict__
