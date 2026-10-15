from odoo.tests import common

from ..models.auth_oauth_provider import OAuthProvider
from .helpers import skip_without_keycloak_admin_credentials


class TestOAuthProvider(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test__action_clean_kc(self):
        skip_without_keycloak_admin_credentials(self)
        self.env["auth.oauth.provider"].action_clean_kc_orphan_users()
