class HTTPError(Exception):
    message = "Network problem accessing API. Exception: \n {}"

    def __init__(self, error_msg):
        self.message = self.message.format(error_msg)
        super().__init__(self.message)


class BadRequestError(Exception):
    message = "BadRequest with the next body: \n {}"

    def __init__(self, body):
        self.message = self.message.format(body)
        super(HTTPError, self).__init__(self.message)


class ResourceNotFound(Exception):
    message = "ResourceNotFound. Resource: {} and filter: {}"

    def __init__(self, resource, filter):
        self.message = self.message.format(resource, filter)
        super().__init__(self.message)


class NotSuccessfulRequest(Exception):
    message = "Response status code is: {}"

    def __init__(self, status_code):
        self.message = self.message.format(status_code)
        super().__init__(self.message)
