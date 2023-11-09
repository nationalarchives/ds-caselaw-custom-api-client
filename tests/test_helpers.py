from requests_toolbelt.multipart import encoder


class MockMultipartResponse:
    def __init__(self, text):
        multipart = encoder.MultipartEncoder({"content": text})
        self.content = multipart.to_string()
        self.headers = {"content-type": multipart.content_type}
