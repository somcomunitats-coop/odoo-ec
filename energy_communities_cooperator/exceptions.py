class ControllerContextValidationError(Exception):
    def __init__(self, http_error_code, title, message):
        self.http_error_code = http_error_code
        self.title = title
        self.message = message

class FormValidationError(Exception):
    def __init__(self, http_error_code, title, messages):
        self.http_error_code = http_error_code
        self.title = title
        self.messages = messages

#TODO: Maybe this should be moved to energy_communities module
class ComponentValidationError(Exception):
    def __init__(self, http_error_code, title, messages):
        self.http_error_code = http_error_code
        self.title = title
        self.messages = messages
