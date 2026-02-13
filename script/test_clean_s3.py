# flake8: ignore=S101
import pytest
from clean_s3 import extract_uri_from_key, should_process_file


class TestShouldProcessFile:
    def test_should_process_file(self):
        assert should_process_file("parser.log", True) is False
        assert should_process_file("file.tar.gz", True) is False
        assert should_process_file("file.pdf", True) is False
        assert should_process_file("file.pdf", False) is True
        assert should_process_file("file.docx", True) is True
        assert should_process_file("image.png", True) is True
        assert should_process_file("image.jpeg", True) is True
        assert should_process_file("image.jpg", True) is True
        with pytest.warns(UserWarning, match="unexpected extension"):
            assert should_process_file("unexpected.txt", True) is False


class TestExtractURIFromKey:
    def test_extract_uri_from_key(self):
        assert extract_uri_from_key("d-a1b2/d-a1b2.pdf") == "d-a1b2"
        assert extract_uri_from_key("uksc/2024/1/uksc_2024_1.docx") == "uksc/2024/1"
        assert extract_uri_from_key("uksc/2024/1/image.jpeg") == "uksc/2024/1"
