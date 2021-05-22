class ParsePageException(Exception):
    def __init__(self, msg, http_body=None, context=None):
        super().__init__(msg)
        self.msg = msg
        self.http_body = http_body
        self.context = context


class BadResponseException(Exception):
    def __init__(self, status_code, context):
        super().__init__(' '.join(('HTTP response', str(status_code))))
        self.status_code = status_code
        self.context = context


class CurlException(Exception):
    def __init__(self, context, ex):
        self.context = context
        self.curl_ex = ex
