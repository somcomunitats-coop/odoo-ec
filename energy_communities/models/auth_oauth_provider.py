import werkzeug

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.auth_oauth.controllers.main import OAuthLogin as OAL

URL_ADMIN_USERS = "{root_endpoint}admin/realms/{realm_name}/users"
URL_AUTH = "{root_endpoint}realms/{realm_name}/protocol/openid-connect/auth"
URL_VALIDATION = "{root_endpoint}realms/{realm_name}/protocol/openid-connect/userinfo"
URL_TOKEN = "{root_endpoint}realms/{realm_name}/protocol/openid-connect/token"
URL_JWKS = "{root_endpoint}realms/{realm_name}/protocol/openid-connect/certs"


class OAuthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    is_admin_provider = fields.Boolean(string="Admin provider")
    is_keycloak_provider = fields.Boolean(string="Keycloak provider")
    superuser = fields.Char(
        string="Superuser",
        help="A super power user that is able to CRUD users on KC.",
        placeholder="admin",
        required=False,
    )
    superuser_pwd = fields.Char(
        string="Superuser password",
        help='"Superuser" user password',
        placeholder='I hope is not "admin"',
        required=False,
    )
    admin_user_endpoint = fields.Char(string="User admin URL", required=True)
    root_endpoint = fields.Char(
        string="Root URL",
        required=True,
        default="http://keycloak-ccee.local:8080/auth/",
    )
    realm_name = fields.Char(string="Realm name", required=True, default="0")

    def validate_admin_provider(self):
        if not self.client_secret:
            raise UserError("Admin provider doesn't have a valid client secret")
        if not self.superuser_pwd:
            raise UserError("Admin provider doesn't have a valid superuser password")

    @api.onchange("root_endpoint")
    def _onchange_root_endpoint(self):
        if self.is_keycloak_provider and self.root_endpoint and self.realm_name:
            self.admin_user_endpoint = URL_ADMIN_USERS.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )
            self.auth_endpoint = URL_AUTH.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )
            self.validation_endpoint = URL_VALIDATION.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )
            self.token_endpoint = URL_TOKEN.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )
            self.jwks_uri = URL_JWKS.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )

    @api.onchange("realm_name")
    def _onchange_realm_name(self):
        if self.is_keycloak_provider and self.root_endpoint and self.realm_name:
            self.admin_user_endpoint = URL_ADMIN_USERS.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )
            self.auth_endpoint = URL_AUTH.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )
            self.validation_endpoint = URL_VALIDATION.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )
            self.token_endpoint = URL_TOKEN.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )
            self.jwks_uri = URL_JWKS.format(
                **{"root_endpoint": self.root_endpoint, "realm_name": self.realm_name}
            )

    def get_auth_link(self):
        self.ensure_one()
        provider_dict = [
            p_dict
            for p_dict in OAL().list_providers()
            if p_dict.get("id") and p_dict.get("id") == self.id
        ]
        return (
            provider_dict and provider_dict[0] and provider_dict[0]["auth_link"] or ""
        )
