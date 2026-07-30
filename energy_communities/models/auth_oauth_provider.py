import logging

import requests
import werkzeug

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.auth_oauth.controllers.main import OAuthLogin as OAL

logger = logging.getLogger(__name__)

URL_ADMIN_USERS = "{root_endpoint}admin/realms/{realm_name}/users"
URL_AUTH = "{root_endpoint}realms/{realm_name}/protocol/openid-connect/auth"
URL_VALIDATION = "{root_endpoint}realms/{realm_name}/protocol/openid-connect/userinfo"
URL_TOKEN = "{root_endpoint}realms/{realm_name}/protocol/openid-connect/token"
URL_JWKS = "{root_endpoint}realms/{realm_name}/protocol/openid-connect/certs"
URL_RESET_PASSWORD = "{root_endpoint}admin/realms/{realm_name}/users/{kc_uid}/execute-actions-email?redirect_uri={odoo_url}&client_id={cliend_id}"


class OAuthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    is_admin_provider = fields.Boolean(string="Admin provider")
    is_keycloak_provider = fields.Boolean(string="Keycloak provider")
    superuser = fields.Char(
        string="Superuser",
        help="A super power user that is able to CRUD users on KC.",
        required=False,
    )
    superuser_pwd = fields.Char(
        string="Superuser password",
        help='"Superuser" user password',
        required=False,
    )
    admin_user_endpoint = fields.Char(string="User admin URL")
    root_endpoint = fields.Char(
        string="Root URL",
        required=True,
        default="http://keycloak-ccee.local:8080/auth/",
    )
    realm_name = fields.Char(string="Realm name", required=True, default="0")
    reset_password_endpoint = fields.Char(string="Reset password URL")
    redirect_admin_url = fields.Char(string="Redirect Link after update password")

    def validate_admin_provider(self):
        if not self.client_secret:
            raise UserError("Admin provider doesn't have a valid client secret")
        if not self.superuser_pwd:
            raise UserError("Admin provider doesn't have a valid superuser password")

    @api.onchange("root_endpoint", "realm_name", "redirect_admin_url")
    def _onchange_update_endpoints(self):
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
            self.reset_password_endpoint = URL_RESET_PASSWORD.format(
                root_endpoint=self.root_endpoint,
                realm_name=self.realm_name,
                kc_uid="{kc_uid}",
                odoo_url=self.redirect_admin_url,
                cliend_id=self.client_id,
            )

    def action_force_reconnect_users_with_keycloak(self):
        """Force massive reconnection of all Odoo users linked to Keycloak.

        Only allowed on non-productive databases (not_productive_database = True).
        Only users with role platform_admin can execute this action.
        Steps:
          1. Check not_productive_database system parameter.
          2. Reset oauth_uid for all users that have one.
          3. Re-push all those users to KC (create or reuse by VAT).
          4. Set email verified, remove required actions, set credentials (login as pwd).
          5. Ensure odoo-allow group assignment.
        """
        self.ensure_one()
        not_productive = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("not_productive_database", default="False")
        )
        if not_productive not in (True, "True", "true", "1"):
            raise UserError(_("This action is not allowed on a production database."))
        users = (
            self.env["res.users"]
            .sudo()
            .search([("oauth_uid", "!=", False), ("active", "in", [True, False])])
        )
        logger.info(
            "force_reconnect_users_with_keycloak: resetting oauth_uid for %d users",
            len(users),
        )
        users.write({"oauth_uid": False})
        users.create_users_on_keycloak()
        provider_id = self.env.ref("energy_communities.keycloak_admin_provider")
        provider_id.validate_admin_provider()
        res_users_model = self.env["res.users"]
        token = res_users_model._get_admin_token(provider_id)
        for user in users:
            if not user.oauth_uid:
                logger.warning(
                    "force_reconnect: user %s has no oauth_uid after push, skipping KC steps",
                    user.login,
                )
                continue
            kc_uid = user.oauth_uid
            user_endpoint = provider_id.admin_user_endpoint + "/" + kc_uid
            headers = {
                "Authorization": "Bearer %s" % token,
                "Content-Type": "application/json",
            }
            # Set emailVerified=True and remove requiredActions
            update_resp = requests.put(
                user_endpoint,
                headers=headers,
                json={"emailVerified": True, "requiredActions": [], "enabled": True},
            )
            if not update_resp.ok:
                logger.error(
                    "force_reconnect: failed to update user %s in KC: %s",
                    user.login,
                    update_resp.text,
                )
            # Set or reset credentials (password = login lowercased, non-temporary)
            credentials_endpoint = user_endpoint + "/reset-password"
            cred_resp = requests.put(
                credentials_endpoint,
                headers=headers,
                json={
                    "type": "password",
                    "value": user.login.lower(),
                    "temporary": False,
                },
            )
            if not cred_resp.ok:
                logger.error(
                    "force_reconnect: failed to set credentials for user %s in KC: %s",
                    user.login,
                    cred_resp.text,
                )
        users.sudo()._assign_kc_user_groups()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Keycloak reconnection completed"),
                "message": _("Users have been reconnected to Keycloak successfully."),
                "sticky": False,
                "type": "success",
            },
        }

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
