import logging
from json import JSONDecodeError

import requests

from odoo import _, api, exceptions, fields, models

logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _name = "res.users"
    _inherit = ["res.users", "user.currentcompany.mixin"]

    _LOGIN_MATCH_KEY = "id:login"

    current_role = fields.Char(computed="_compute_current_role", store=False)

    def _compute_current_role(self):
        for record in self:
            record.current_role = record.get_current_role()

    def _generate_signup_values(self, provider, validation, params):
        """
        Overwrite method to get user values with user_id not email
        :param provider:
        :param validation:
        :param params:
        :return:
        """
        values = super()._generate_signup_values(provider, validation, params)
        values["login"] = validation["user_id"]
        return values

    def _get_admin_token(self, provider_id):
        """Retrieve auth token from Keycloak."""
        url = provider_id.token_endpoint.replace("/introspect", "")
        logger.info("Calling %s" % url)
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "username": provider_id.superuser,
            "password": provider_id.superuser_pwd,
            "grant_type": "password",
            "client_id": provider_id.client_id,
            "client_secret": provider_id.client_secret,
        }
        resp = requests.post(url, data=data, headers=headers)
        self._validate_response(resp)
        return resp.json()["access_token"]

    def create_users_on_keycloak(self):
        """Create users on Keycloak.

        1. get a token
        2. loop on given users
        3. push them to Keycloak if:
           a. missing on Keycloak
           b. they do not have an Oauth UID already
        4. brings you to update users list
        """
        logger.debug("Create keycloak user START")
        provider_id = self.env.ref("energy_communities.keycloak_admin_provider")
        provider_id.validate_admin_provider()
        token = self._get_admin_token(provider_id)
        logger.info("Creating users for %s" % ",".join(self.mapped("login")))
        for user in self:
            if user.oauth_uid:
                # already sync'ed somewhere else
                continue
            keycloak_user = self._get_or_create_kc_user(token, provider_id, user)
            keycloak_key = self._LOGIN_MATCH_KEY.split(":")[0]
            keycloak_login_provider = self.env.ref(
                "energy_communities.keycloak_login_provider"
            )
            user.update(
                {
                    "oauth_uid": keycloak_user[keycloak_key],
                    "oauth_provider_id": keycloak_login_provider.id,
                }
            )
        # action = self.env.ref('base.action_res_users').read()[0]
        # action['domain'] = [('id', 'in', self.user_ids.ids)]
        logger.debug("Create keycloak users STOP")
        return True

    def _get_kc_users(self, token, provider_id, **params):
        """Retrieve users from Keycloak.

        :param token: a valida auth token from Keycloak
        :param **params: extra search params for users endpoint
        """
        logger.info("Calling %s" % provider_id.admin_user_endpoint)
        headers = {
            "Authorization": "Bearer %s" % token,
        }
        resp = requests.get(
            provider_id.admin_user_endpoint, headers=headers, params=params
        )
        self._validate_response(resp)
        return resp.json()

    def _validate_response(self, resp, no_json=False):
        # When Keycloak detects a clash on non-unique values, like emails,
        # it raises:
        # `HTTPError: 409 Client Error: Conflict for url: `
        # http://keycloak:8080/auth/admin/realms/master/users
        if resp.status_code == 409:
            detail = ""
            if resp.content and resp.json().get("errorMessage"):
                # ie: {"errorMessage":"User exists with same username"}
                detail = "\n" + resp.json().get("errorMessage")
            raise exceptions.UserError(
                _(
                    "Conflict on user values. "
                    "Please verify that all values supposed to be unique "
                    "are really unique. %(detail)s"
                )
                % {"detail": detail}
            )
        if not resp.ok:
            # TODO: do something better?
            raise resp.raise_for_status()
        if no_json:
            return resp.content
        try:
            return resp.json()
        except JSONDecodeError:
            raise exceptions.UserError(_("Something went wrong. Please check logs."))

    def _get_or_create_kc_user(self, token, provider_id, odoo_user):
        """Lookup for given user on Keycloak: create it if missing.

        :param token: valid auth token from Keycloak
        :param odoo_user: res.users record
        """
        odoo_key = self._LOGIN_MATCH_KEY.split(":")[1]
        keycloak_user = self._get_kc_users(
            token, provider_id, search=odoo_user.mapped(odoo_key)[0]
        )
        if keycloak_user:
            if len(keycloak_user) > 1:
                # TODO: warn user?
                pass
            return keycloak_user[0]
        else:
            values = self._create_user_values(odoo_user)
            keycloak_user = self._create_kc_user(token, provider_id, **values)
        return keycloak_user

    def _create_user_values(self, odoo_user):
        """Prepare Keycloak values for given Odoo user."""
        values = {
            "username": odoo_user.login,
            "email": odoo_user.partner_id.email,
            "attributes": {"lang": [odoo_user.lang]},
            "enabled": True,
        }

        if "firstname" in odoo_user.partner_id:
            # partner_firstname installed
            firstname = odoo_user.partner_id.firstname
            lastname = odoo_user.partner_id.lastname
        else:
            firstname, lastname = self._split_user_fullname(odoo_user)
        values.update(
            {
                "firstName": firstname,
                "lastName": lastname,
            }
        )
        logger.debug("CREATE using values %s" % str(values))
        return values

    def _split_user_fullname(self, odoo_user):
        # yeah, I know, it's not perfect... you can override it ;)
        name_parts = odoo_user.name.split(" ")
        if len(name_parts) == 2:
            # great we've found the 2 parts
            firstname, lastname = name_parts
        else:
            # make sure firstname is there
            # then use the rest - if any - to build lastname
            firstname, lastname = name_parts[0], " ".join(name_parts[1:])
        return firstname, lastname

    def _create_kc_user(self, token, provider_id, **data):
        """Create a user on Keycloak w/ given data."""
        logger.info("CREATE Calling %s" % provider_id.admin_user_endpoint)
        headers = {
            "Authorization": "Bearer %s" % token,
        }
        # TODO: what to do w/ credentials?
        # Shall we just rely on Keycloak sending out a reset password link?
        # Shall we enforce a dummy pwd and enable "change after 1st login"?
        resp = requests.post(
            provider_id.admin_user_endpoint, headers=headers, json=data
        )
        self._validate_response(resp, no_json=True)
        # yes, Keycloak sends back NOTHING on create
        # so we are forced to do anothe call to get its data :(
        return self._get_kc_users(token, provider_id, search=data["username"])[0]

    # TODO: Modify this method to make it compatible with currentuser mixin
    def get_role_codes(self):
        # TODO Map all code to company and enable (We should update the API schema too)
        return self.role_line_ids[0].role_id.code

    def send_reset_password_mail(self):
        provider_id = self.env.ref("energy_communities.keycloak_admin_provider")
        provider_id.validate_admin_provider()
        headers = {"Authorization": "Bearer %s" % self._get_admin_token(provider_id)}
        headers["Content-Type"] = "application/json"
        if provider_id.reset_password_endpoint:
            endpoint = provider_id.reset_password_endpoint.format(kc_uid=self.oauth_uid)
            response = requests.put(
                endpoint, headers=headers, data='["UPDATE_PASSWORD", "VERIFY_EMAIL"]'
            )
        else:
            raise exceptions.UserError(_("Reset password url is not set."))
        if response.status_code != 204:
            raise exceptions.UserError(
                _(
                    "Something went wrong. Mail can not be sended. More details: {}"
                ).format(response.json())
            )

    def make_internal_user(self):
        already_user = self.env["res.users.role.line"].search(
            [
                ("user_id.id", "=", self.id),
                ("active", "=", True),
                ("role_id.code", "=", "role_internal_user"),
            ]
        )
        if not already_user:
            role = self.env.ref("energy_communities.role_internal_user")
            self.write(
                {
                    "role_line_ids": [
                        (
                            0,
                            0,
                            {
                                "user_id": self.id,
                                "active": True,
                                "role_id": role.id,
                            },
                        )
                    ]
                }
            )

    def make_ce_user(self, company_id, role_name):
        role = self.env["res.users.role"].search([("code", "=", role_name)])
        current_role = self.env["res.users.role.line"].search(
            [
                ("user_id", "=", self.id),
                ("active", "=", True),
                ("company_id", "=", company_id),
            ]
        )

        if current_role:
            current_role.write({"role_id": role})
        else:
            self.write(
                {
                    "company_ids": [(4, company_id)],
                    "role_line_ids": [
                        (
                            0,
                            0,
                            {
                                "user_id": self.id,
                                "active": True,
                                "role_id": role.id,
                                "company_id": company_id,
                            },
                        )
                    ],
                }
            )

    def make_coord_user(self, company_id, role_name):
        # create ce user on this company
        self.make_ce_user(company_id, role_name)
        # apply manager role the child companies
        company = self.env["res.company"].browse(company_id)
        child_companies = company.get_child_companies()
        for child_company in child_companies:
            self.make_ce_user(child_company.id, "role_ce_manager")

    def add_energy_community_role(self, company_id, role_name):
        if role_name == "role_ce_member" or role_name == "role_ce_admin":
            self.make_ce_user(company_id, role_name)
        elif role_name == "role_coord_worker" or role_name == "role_coord_admin":
            self.make_coord_user(company_id, role_name)
        else:
            raise exceptions.UserError(_("Role not found"))

    def create_energy_community_base_user(
        cls, vat, first_name, last_name, lang_code, email
    ):
        vals = {
            "login": vat,
            "firstname": first_name,
            "lastname": last_name,
            "lang": lang_code,
            "email": email,
        }
        user = cls.sudo().with_context(no_reset_password=True).create(vals)
        user.make_internal_user()
        user.create_users_on_keycloak()
        user.send_reset_password_mail()

        return user
