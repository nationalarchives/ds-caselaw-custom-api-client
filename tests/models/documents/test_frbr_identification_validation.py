import pytest
from lxml import etree

from caselawclient.models.documents.body_metadata.frbr_identification_validation import (
    frbr_identification_validation_failure,
    is_valid_frbr_identification,
)
from caselawclient.xml_helpers import DEFAULT_NAMESPACES
from tests.models.documents.body_metadata.fixtures import (
    AKN_NS,
    UK_NS,
    akn_child,
    fresh_valid_identification,
    read_fixture,
)


def _identification_from_bytes(xml: bytes) -> etree._Element:
    root = etree.fromstring(xml)
    return root.xpath("//akn:identification", namespaces=DEFAULT_NAMESPACES)[0]


class TestFrbrIdentificationValidation:
    def test_valid_triple_passes(self):
        assert is_valid_frbr_identification(fresh_valid_identification())

    def test_work_only_identification_fails(self):
        identification = _identification_from_bytes(read_fixture("work_only_identification.xml"))

        reason = frbr_identification_validation_failure(identification)

        assert reason is not None
        assert "FRBRExpression" in reason

    def test_rejects_non_identification_node(self):
        identification = fresh_valid_identification()
        work = identification[0]

        reason = frbr_identification_validation_failure(work)

        assert reason == "node is not an identification element"

    def test_rejects_identification_in_wrong_namespace(self):
        identification = etree.Element(f"{{{UK_NS}}}identification", source="#tna")

        reason = frbr_identification_validation_failure(identification)

        assert reason == "identification is not in the Akoma Ntoso namespace"

    def test_rejects_missing_source_attribute(self):
        identification = fresh_valid_identification()
        identification.attrib.pop("source")

        reason = frbr_identification_validation_failure(identification)

        assert reason == "identification is missing a source attribute"

    @pytest.mark.parametrize(
        ("child_local_name", "expected_reason"),
        [
            ("FRBRWork", "identification is missing FRBRWork"),
            ("FRBRManifestation", "identification is missing FRBRManifestation"),
        ],
    )
    def test_rejects_missing_frbr_triple_member(self, child_local_name, expected_reason):
        identification = fresh_valid_identification()
        identification.remove(akn_child(identification, child_local_name))

        reason = frbr_identification_validation_failure(identification)

        assert reason == expected_reason

    @pytest.mark.parametrize(
        ("extra_element", "expected_reason"),
        [
            (f"{{{AKN_NS}}}lifecycle", "identification has unexpected children: lifecycle"),
            ("{http://example.com/ns}foreign", "identification has unexpected children: foreign"),
        ],
    )
    def test_rejects_unexpected_identification_sibling(self, extra_element, expected_reason):
        identification = fresh_valid_identification()
        etree.SubElement(identification, extra_element)

        reason = frbr_identification_validation_failure(identification)

        assert reason == expected_reason

    @pytest.mark.parametrize(
        ("level_local_name", "required_child", "expected_reason"),
        [
            ("FRBRWork", "FRBRcountry", "FRBRWork is missing FRBRcountry"),
            ("FRBRExpression", "FRBRlanguage", "FRBRExpression is missing FRBRlanguage"),
            ("FRBRManifestation", "FRBRformat", "FRBRManifestation is missing FRBRformat"),
        ],
    )
    def test_rejects_missing_required_child(self, level_local_name, required_child, expected_reason):
        identification = fresh_valid_identification()
        level = akn_child(identification, level_local_name)
        level.remove(akn_child(level, required_child))

        reason = frbr_identification_validation_failure(identification)

        assert reason == expected_reason

    def test_rejects_empty_frbrthis_value(self):
        identification = fresh_valid_identification()
        work = akn_child(identification, "FRBRWork")
        akn_child(work, "FRBRthis").set("value", "   ")

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRWork/FRBRthis is missing a value attribute"

    def test_rejects_missing_frbrauthor_href(self):
        identification = fresh_valid_identification()
        work = akn_child(identification, "FRBRWork")
        akn_child(work, "FRBRauthor").attrib.pop("href")

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRWork/FRBRauthor is missing an href attribute"

    def test_rejects_missing_frbrdate_on_work(self):
        identification = fresh_valid_identification()
        work = akn_child(identification, "FRBRWork")
        work.remove(akn_child(work, "FRBRdate"))

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRWork is missing FRBRdate"

    def test_rejects_empty_decision_frbrdate(self):
        identification = fresh_valid_identification()
        work = akn_child(identification, "FRBRWork")
        akn_child(work, "FRBRdate").set("date", "")

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRWork/FRBRdate is missing a date attribute"

    def test_rejects_duplicate_frbrname_on_work(self):
        identification = fresh_valid_identification()
        work = akn_child(identification, "FRBRWork")
        etree.SubElement(work, f"{{{AKN_NS}}}FRBRname", value="first")
        etree.SubElement(work, f"{{{AKN_NS}}}FRBRname", value="second")

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRWork has multiple FRBRname elements"

    def test_rejects_unexpected_child_under_work(self):
        identification = fresh_valid_identification()
        work = akn_child(identification, "FRBRWork")
        etree.SubElement(work, f"{{{AKN_NS}}}NotInSchema")

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRWork has unexpected child NotInSchema"

    def test_rejects_empty_expression_language(self):
        identification = fresh_valid_identification()
        expression = akn_child(identification, "FRBRExpression")
        akn_child(expression, "FRBRlanguage").set("language", "  ")

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRExpression/FRBRlanguage is missing a language attribute"

    def test_rejects_non_akn_child_under_work(self):
        identification = fresh_valid_identification()
        work = akn_child(identification, "FRBRWork")
        work.insert(0, etree.Element("{http://example.com/ns}foreign"))

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRWork contains a non-AKN child"

    def test_rejects_out_of_order_work_children(self):
        identification = fresh_valid_identification()
        work = akn_child(identification, "FRBRWork")
        work.insert(0, etree.Element(f"{{{AKN_NS}}}FRBRname", value="Before FRBRthis"))

        reason = frbr_identification_validation_failure(identification)

        assert reason == "FRBRWork child elements are not in schema order"
