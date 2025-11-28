class ContextValidationError(Exception):
    def __init__(self, http_error_code, title, message):
        self.http_error_code = http_error_code
        self.title = title
        self.message = message
