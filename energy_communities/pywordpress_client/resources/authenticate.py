from ..client import Client


class Authenticate:
    _name = "authenticate"
    _url_path = "/jwt-auth/v1/token"

    def __init__(self, baseurl, username, password):
        self.baseurl = baseurl
        self.username = username
        self.password = password

    def authenticate(self):
        """
        Get auth token
        """
        response_data = Client(self.baseurl).post(
            "{}".format(self._url_path),
            body={"username": self.username, "password": self.password},
        )

        return response_data
