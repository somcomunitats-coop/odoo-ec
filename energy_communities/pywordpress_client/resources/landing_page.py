from ..client import Client


class LandingPage:
    _name = "landing_page"
    _url_path = "/wp/v2/rest-ce-landing"

    def __init__(self, token, baseurl, id=False):
        self.baseurl = baseurl
        self.token = token
        self.id = id

    def get(self):
        """
        Get Landing Page data.
        """
        response_data = Client(self.baseurl).get(
            "{url_path}/{id}".format(url_path=self._url_path, id=self.id), self.token
        )
        return response_data

    def create(self, body):
        """
        Creates a Landing Page instance.
        """
        response_data = Client(self.baseurl).post(
            "{}".format(self._url_path), self.token, body
        )
        return response_data

    def update(self, body):
        """
        Updates a Landing Page instance.
        """
        response_data = Client(self.baseurl).put(
            "{url_path}/{id}".format(url_path=self._url_path, id=self.id),
            self.token,
            body,
        )
        return response_data
