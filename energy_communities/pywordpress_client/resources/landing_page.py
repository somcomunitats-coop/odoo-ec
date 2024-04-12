from ..client import Client


class LandingPage:
    _name = "landing_page"
    _url_path = "/wpct-remote/v1"

    def __init__(self, token, baseurl, company_hierarchy_level, id=False):
        self.baseurl = baseurl
        self.token = token
        self.id = id
        self.company_hierarchy_level = company_hierarchy_level

    def get(self):
        """
        Get Landing Page data.
        """
        response_data = Client(self.baseurl).get(
            "{url_path}/{company_hierarchy_level}/{id}".format(
                url_path=self._url_path,
                company_hierarchy_level=self.company_hierarchy_level,
                id=self.id,
            ),
            self.token,
        )
        return response_data

    def create(self, body):
        """
        Creates a Landing Page instance.
        """
        response_data = Client(self.baseurl).post(
            "{url_path}/{company_hierarchy_level}".format(
                url_path=self._url_path,
                company_hierarchy_level=self.company_hierarchy_level,
            ),
            self.token,
            body,
        )
        return response_data

    def update(self, body):
        """
        Updates a Landing Page instance.
        """
        response_data = Client(self.baseurl).put(
            "{url_path}/{company_hierarchy_level}/{id}".format(
                url_path=self._url_path,
                company_hierarchy_level=self.company_hierarchy_level,
                id=self.id,
            ),
            self.token,
            body,
        )
        return response_data
