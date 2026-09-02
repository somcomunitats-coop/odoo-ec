from odoo import http
from odoo.tests.common import HOST, HttpCase, Opener, get_db_name


class TestSessionLogout(HttpCase):
    def setUp(self):
        super().setUp()
        self.session = http.root.session_store.new()
        self.session.update(http.get_default_session(), db=get_db_name())
        self.opener = Opener(self.env.cr)
        self.opener.cookies.set("session_id", self.session.sid, domain=HOST, path="/")

    def login(self, username, password, csrf_token=None):
        """Log in with provided credentials and return response to POST request or raises for status."""
        res_post = self.url_open(
            "/web/login",
            data={
                "login": username,
                "password": password,
                "csrf_token": csrf_token or http.Request.csrf_token(self),
            },
            timeout=500,
        )
        res_post.raise_for_status()
        return res_post

    def test_logout(self):
        self.login("42281799W", "1234")
        res = self.url_open("/web/session/logout", timeout=500)
        self.assertEqual(res.request.url, 200)
