from ..client import Client


class Authenticate:
    _name = "authenticate"
    _url_path = "/jwt-auth/v1/token"

    def __init__(self, username, password, token=None, **kwargs):
        self.username = username
        self.password = password
        self.token = token

    def authenticate(self):
        """
        Get auth token
        """
        response_data = Client().post(
            "{}".format(self._url_path),
            body={"username": self.username, "password": self.password},
        )

        return response_data
