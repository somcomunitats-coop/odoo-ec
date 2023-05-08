from ..client import Client
from .. import helpers


class Authenticate:
    _name = "authenticate"
    _url_path = "/jwt-auth/v1/token"

    def __init__(self, username=None, password=None, token=None, **kwargs):
        self.username = helpers.getenv_or_fail("USERNAME")
        self.password = helpers.getenv_or_fail("PASSWORD")
        self.token = "Bearer %s" % token

    def authenticate(self):
        """
        Get auth token
        """
        response_data = Client().post(
            "{}".format(self._url_path),
            body={"username": self.username, "password": self.password},
        )

        return response_data
