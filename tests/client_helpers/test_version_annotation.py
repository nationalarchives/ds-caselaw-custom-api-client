import pytest

from caselawclient.models.documents.versions import VersionAnnotation, VersionType


class TestVersionAnnotation:
    def test_structured_annotation_dict_returns_expected_values(self):
        annotation = VersionAnnotation(
            VersionType.SUBMISSION,
            message="test_structured_annotation_dict_returns_expected_values",
            payload={"test_payload": True},
            automated=False,
        )
        annotation.set_calling_agent("marklogic-api-client-test")
        annotation.set_calling_function("update_xml")

        assert annotation.structured_annotation_dict == {
            "automated": False,
            "calling_agent": "marklogic-api-client-test",
            "calling_function": "update_xml",
            "message": "test_structured_annotation_dict_returns_expected_values",
            "payload": {"test_payload": True},
            "type": "submission",
        }

    def test_structured_annotation_dict_raises_on_no_calling_function_name(self):
        annotation = VersionAnnotation(
            VersionType.SUBMISSION,
            message="test_structured_annotation_dict_raises_on_no_calling_function_name",
            automated=False,
        )
        annotation.set_calling_agent("marklogic-api-client-test")

        with pytest.raises(AttributeError) as e:
            annotation.structured_annotation_dict

        assert str(e.value) == "The name of the calling function has not been set; use set_calling_function()"

    def test_structured_annotation_dict_raises_on_no_calling_agent(self):
        annotation = VersionAnnotation(
            VersionType.SUBMISSION,
            message="test_structured_annotation_dict_raises_on_no_calling_agent",
            automated=False,
        )
        annotation.set_calling_function("update_xml")

        with pytest.raises(AttributeError) as e:
            annotation.structured_annotation_dict

        assert str(e.value) == "The name of the calling agent has not been set; use set_calling_agent()"
