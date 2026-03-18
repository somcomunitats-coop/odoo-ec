from http import HTTPStatus


class ValidationError(Exception):
    """
    Base error class for manage Validation Errors
    """

    http_error_code = HTTPStatus.BAD_REQUEST

    def __init__(self, title, message):
        self.title = title
        self.message = message

    def __str__(self):
        class_name = self.__class__.__name__
        return f"{class_name}: {self.message}"


class ControllerContextValidationError(ValidationError):
    """
    We will raise this error when something goes wrong processing the
    request (URL, parameters...)
    """

    ...


class URLValidationError(ValidationError):
    """
    If the requests match the url route but the path has missing values or incorrect ones
    """

    http_error_code = HTTPStatus.NOT_FOUND


class FormValidationError(ValidationError):
    """
    We will raise this error when our forms contain some errors
    """

    def __init__(self, title, messages):
        self.title = title
        self.messages = messages
        self.message = "\n".join(messages)


class ComponentValidationError(FormValidationError):
    """
    This error occurs when there are validation errors inside of a component
    """

    http_error_code = HTTPStatus.UNPROCESSABLE_ENTITY
