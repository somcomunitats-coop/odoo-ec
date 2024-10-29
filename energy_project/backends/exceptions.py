class BackendError(Exception):
    """
    Base class for custom exceptions for handling errors in backends implementations
    """

    ...


class RequestError(BackendError):
    def __init__(self, error_code, message):
        self.error_code = error_code
        self.message = message


class UrlNotFoundError(BackendError):
    def __init__(self, function):
        self.message = "There is no endpoint defined for {function}".format(
            function=function
        )
