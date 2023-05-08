from ..client import Client


class LandingPage:
    _name = "landing_page"
    _url_path = "/wp/v2/rest-ce-landing"

    def __init__(self, id, **kwargs):
        self.id = id

    @classmethod
    def create(cls, token, body):
        """
        Creates a Landing Page instance.
        """
        response_data = Client().post(
            "{}".format(cls._url_path),
            token,
            body
        )

        return cls(**response_data)

    def update(cls, token, body):
        """
        Updates a Landing Page instance.
        """
        response_data = Client().put(
            "{}".format(cls._url_path +self.id),
            token,
            body
        )

        return response_data
