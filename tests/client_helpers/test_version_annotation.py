import pytest

from caselawclient.client_helpers import VersionAnnotation, VersionType


class TestSaveCopyDeleteJudgment:
    def test_structured_annotation_dict_raises_on_no_calling_function_name(self):
        with pytest.raises(AttributeError):
            VersionAnnotation(
                VersionType.SUBMISSION,
                message="test_structured_annotation_dict_raises_on_no_calling_function_name",
            ).structured_annotation_dict
