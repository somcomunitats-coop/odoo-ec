import logging
import re
from datetime import datetime
from json import JSONDecodeError

import requests

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)

_DEFAULT_COOPERATIVE_MEMBERSHIP_USER_ROLE = "role_ce_member"


class ResUsers(models.Model):
    _name = "res.users"
    _inherit = ["res.users", "user.currentcompany.mixin"]

    _LOGIN_MATCH_KEY = "id:login"
    _KC_CLIENT_AUTH_ACCESS_GROUP_ODOO = "odoo-allow"

    # TODO: Delete this field because it's included on the current_company_mixin
    current_role = fields.Char(compute="_compute_current_role", store=False)

    last_user_invitation_through_kc = fields.Datetime(
        string=_("Last user invitation through Keycloak")
    )

    # TODO: Delete this field because it's included on the current_company_mixin
    def _compute_current_role(self):
        for record in self:
            record.current_role = record.get_current_role()

    @api.model_create_multi
    def create(self, vals):
        user = super().create(vals)
        for val in vals:
            if "login" in val.keys():
                partner = self._find_existing_related_partner(val)
                if partner:
                    target_company_ids = partner.company_ids | user.company_ids
                    partner.write({"company_ids": target_company_ids})
                    user.write(
                        {"partner_id": partner.id, "company_ids": target_company_ids}
                    )
        return user

    @api.constrains("lang")
    def constrains_user_lang(self):
        for record in self:
            if record.lang and record.oauth_uid:
                record._update_kc_user_lang()

    @api.constrains("login")
    def constrains_user_login(self):
        for record in self:
            if record.partner_id:
                record.partner_id.write(
                    {
                        "vat": self.login,
                        "country_id": self.env.ref("base.es").id,
                    }
                )

    @api.constrains("partner_id")
    def constrains_user_partner_id(self):
        for record in self:
            if len(record.partner_id.user_ids) > 1:
                raise ValidationError(
                    _(
                        "You cannot link more than one user to a partner. Please check partner {}"
                    ).format(record.partner_id.id)
                )

    @api.constrains("company_ids")
    def constrains_user_partner_id_company_ids(self):
        for record in self:
            record.equalize_user_partner_id_company_ids()

    def equalize_user_partner_id_company_ids(self):
        self.partner_id.write({"company_ids": self.company_ids})
        return True

    def _find_existing_related_partner(self, vals):
        query = [("vat", "=", vals["login"]), ("id", "!=", self.partner_id.id)]
        existing_partners = self.env["res.partner"].sudo().search(query, order="id asc")
        if existing_partners:
            return existing_partners[0]
        return False

    def get_user_auth_access_to_spaces(self):
        _odoo_auth_roles = [
            self.env.ref("energy_communities.role_platform_admin"),
            self.env.ref("energy_communities.role_coord_admin"),
            self.env.ref("energy_communities.role_ce_admin"),
        ]
        _app_auth_roles = [self.env.ref("energy_communities.role_ce_member")]
        _forum_auth_roles = _odoo_auth_roles + _app_auth_roles
        _tech_spaces = {
            "odoo": _odoo_auth_roles,
            "forum": _forum_auth_roles,
            "app": _app_auth_roles,
        }
        user_access = {}
        for record in self:
            user_roles = self.env["res.users.role.line"].search(
                [("user_id", "=", record.id)]
            )
            for space, roles in _tech_spaces.items():
                user_access[space] = False
                for role in user_roles:
                    if role.role_id in roles:
                        user_access[space] = True
        return user_access

    def action_open_form_view(self):
        self.ensure_one()
        form_view = self.env.ref("base.view_users_form")
        return {
            "name": _("Users"),
            "res_model": "res.users",
            "res_id": self.id,
            "views": [
                (form_view.id, "form"),
            ],
            "type": "ir.actions.act_window",
            "target": "self",
        }

    #########################
    # ROLES
    #########################
    def _get_enabled_roles(self):
        active_roles = self.env["res.users.role.line"]
        global_role_lines = active_roles.search(
            [
                ("user_id", "=", self.id),
                ("company_id", "=", None),
            ]
        )
        common_global_role_lines = global_role_lines.filtered(
            lambda r: r.role_id.application_scope
            == self.env["res.users.role"].COMMON_LAYER
        )
        company_ids = (
            self.env.context.get("active_company_ids")
            or self.env.context.get("allowed_company_ids")
            or self.company_id.ids
        )
        company_role_lines = active_roles.search(
            [
                ("user_id", "=", self.id),
                ("company_id", "=", company_ids[0]),
            ]
        )
        active_roles = active_roles | global_role_lines | company_role_lines
        return self._max_priority_role_line(active_roles) | common_global_role_lines

    def _set_user_roles(self, company_id, role_id):
        self._check_role_can_be_assingned(company_id, role_id)
        return self._create_user_role_line(company_id, role_id)

    def _check_role_can_be_assingned(self, company_id, role_id):
        user_roles = [
            "role_platform_admin",
            "role_coord_admin",
            "role_ce_admin",
            "role_ce_manager",
            "role_ce_member",
        ]
        company_hierarchy_level = ["instance", "community", "coordinator"]
        role_is_available_for_company = all(
            [
                company_id.hierarchy_level in company_hierarchy_level,
                role_id.code in company_id.available_role_ids.mapped("code"),
            ]
        )
        if role_is_available_for_company:
            for user_role in self.role_line_ids.mapped("role_id"):
                user_has_role_in_company = all(
                    [
                        user_role.code in user_roles,
                        role_id.code in user_role.available_role_ids.mapped("code"),
                        role_id.priority == user_role.priority,
                        company_id.id == self.company_id.id,
                    ]
                )

                role_is_not_available_for_user = all(
                    [
                        user_role.code in user_roles,
                        role_id.code not in user_role.available_role_ids.mapped("code"),
                    ]
                )

                if user_has_role_in_company:
                    error = _(
                        "User with vat {} is already {} for the company {}"
                    ).format(self.login, user_role.code, company_id.name)
                    raise ValidationError(error)
                if role_is_not_available_for_user:
                    error = _(
                        "Role {} is not available for user with {} role. This role only allows {}"
                    ).format(
                        role_id.code,
                        user_role.code,
                        ", ".join(user_role.available_role_ids.mapped("code")),
                    )
                    raise ValidationError(error)
            return True

        error = _(
            "Role {} is not available for company {} of type {}. This type of company allows roles {}"
        ).format(
            role_id.code,
            company_id.name,
            company_id.hierarchy_level,
            ", ".join(company_id.available_role_ids.mapped("code")),
        )
        raise ValidationError(error)

    def _create_internal_user_role_line(self):
        internal_user = self.env.ref("energy_communities.role_internal_user").id
        internal_user_role = self.env["res.users.role.line"].search(
            [
                ("user_id", "=", self.id),
                ("role_id", "=", internal_user),
            ]
        )
        if not internal_user_role:
            self.env["res.users.role.line"].create(
                {
                    "user_id": self.id,
                    "role_id": internal_user,
                }
            )

    def _create_user_role_line(self, company_id, role_id):
        if not self.login_date:
            self._create_internal_user_role_line()
        user_roles = self.env["res.users.role.line"].search(
            [
                ("user_id", "=", self.id),
                ("role_id", "=", role_id.id),
                ("company_id", "=", company_id.id),
            ]
        )
        if not user_roles:
            self.env["res.users.role.line"].create(
                {
                    "user_id": self.id,
                    "role_id": role_id.id,
                    "company_id": company_id.id,
                }
            )

    def get_user_role_lines(self, company_id=False, role_codes=False):
        query = [("user_id", "=", self.id)]
        if company_id:
            query.append(("company_id", "=", company_id))
        if role_codes:
            query.append(("role_id.code", "in", role_codes))
        return self.env["res.users.role.line"].search(query)

    #########################
    # USER_CREATOR
    #########################
    def make_internal_user(self):
        self._create_internal_user_role_line()

    def make_ce_user(self, company_id, role_name):
        related_company = self.company_ids.filtered(
            lambda company: company.id == company_id
        )
        if not related_company:
            self.write({"company_ids": [(4, company_id)]})
        current_role = self.env["res.users.role.line"].search(
            [
                ("user_id", "=", self.id),
                ("active", "=", True),
                ("company_id", "=", company_id),
                ("code", "=", role_name),
            ]
        )
        if not current_role:
            role = self.env["res.users.role"].search([("code", "=", role_name)])
            self.sudo()._set_user_roles(
                self.env["res.company"].browse(company_id),
                self.env.ref("energy_communities.{}".format(role_name)),
            )

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
        user._send_kc_reset_password_mail()
        return user

    @api.model
    def build_platform_user(
        self,
        company_id,
        partner_id,
        role_id,
        action,
        force_invite,
        user_vals,
    ):
        if partner_id:
            user_vals = {
                "partner_id": partner_id.id,
                "login": partner_id.vat,
                "email": partner_id.email,
                "firstname": partner_id.firstname,
                "lastname": partner_id.lastname,
                "lang": partner_id.lang,
            }
        else:
            self._user_vals_validator(user_vals)

        user = self.env["res.users"].search(
            [
                ("login", "=", user_vals["login"]),
                "|",
                ("active", "=", True),
                ("active", "=", False),
            ]
        )
        if user:
            if company_id not in user.company_ids:
                # add the company to the user's companies
                user.company_ids = [(4, company_id.id, 0)]
            else:
                # set the company as the only company of the user
                company_ids = [(6, 0, [company_id.id])]
                if not user.active:
                    user.sudo().write(
                        {
                            "active": True,
                            "company_id": company_id.id,
                            "company_ids": company_ids,
                        }
                    )
                    user_roles = self.env["res.users.role.line"].search(
                        [("user_id", "=", user.id)]
                    )
                    user_roles.unlink()
        else:
            user_vals["company_id"] = company_id.id
            user_vals["company_ids"] = partner_id.company_ids
            user = self.sudo().with_context(no_reset_password=True).create(user_vals)

        user.sudo()._set_user_roles(company_id, role_id)

        if action in ("create_kc_user", "invite_user_through_kc"):
            user.create_users_on_keycloak()
            user._assign_kc_user_groups()

        if (
            force_invite
            or (
                action == "invite_user_through_kc"
                and not user.last_user_invitation_through_kc
            )
        ) and user.oauth_uid:
            user._send_kc_reset_password_mail()

        return user

    # VALIDATORS
    def _user_vals_validator(self, user_vals):
        if user_vals.keys() != {"login", "email", "firstname", "lastname", "lang"}:
            raise ValidationError(_("User_vals dict is empty"))
        if user_vals["login"] is None:
            raise ValidationError(_("Login is empty"))
        if not self._email_validator(user_vals["email"]):
            raise ValidationError(_("Email is not valid"))
        if not self._lang_validator(user_vals["lang"]):
            raise ValidationError(_("Lang is not valid"))

    def _email_validator(email):
        regex = re.compile(
            r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
        )
        if re.fullmatch(regex, email):
            return True

    def _lang_validator(lang):
        regex = re.compile(r"/[a-z]{2}_[A-Z]{2}/gm")
        if re.fullmatch(regex, lang):
            return True
        return False

    #########################
    # KEYCLOAK
    #########################
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

    def _get_kc_groups(self, token, provider_id, **params):
        """Retrieve user groups from Keycloak.

        :param token: a valida auth token from Keycloak
        :param **params: extra search params for user groups endpoint
        """
        # GET /{realm}/groups
        groups_endpoint = provider_id.admin_user_endpoint.replace("users", "groups")
        logger.info("Calling GET %s" % groups_endpoint)
        headers = {
            "Authorization": "Bearer %s" % token,
        }
        resp = requests.get(groups_endpoint, headers=headers, params=params)
        self._validate_response(resp)
        return resp.json()

    def _get_kc_user_groups(self, token, provider_id, odoo_user, **params):
        """Retrieve user groups from Keycloak.

        :param token: a valida auth token from Keycloak
        :param **params: extra search params for user groups endpoint
        """
        # GET /{realm}/users/{id}/groups
        user_groups_endpoint = (
            provider_id.admin_user_endpoint + "/" + odoo_user.oauth_uid + "/groups"
        )
        logger.info("Calling GET %s" % user_groups_endpoint)
        headers = {
            "Authorization": "Bearer %s" % token,
        }
        resp = requests.get(user_groups_endpoint, headers=headers, params=params)
        self._validate_response(resp)
        return resp.json()

    def _add_kc_user_groups(self, token, provider_id, odoo_user, kc_group_id):
        """Put user groups from Keycloak."""
        # PUT /{realm}/users/{id}/groups/{groupId}
        user_groups_endpoint = (
            provider_id.admin_user_endpoint
            + "/"
            + odoo_user.oauth_uid
            + "/groups/"
            + kc_group_id
        )
        logger.info("Calling PUT %s" % user_groups_endpoint)
        headers = {
            "Authorization": "Bearer %s" % token,
        }
        resp = requests.put(user_groups_endpoint, headers=headers)
        self._validate_response(resp, no_json=True)
        # yes, Keycloak sends back NOTHING on create
        # so we are forced to do another call to get its data :(
        return self._get_kc_user_groups(token, provider_id, odoo_user)

    def _remove_kc_user_groups(self, token, provider_id, odoo_user, kc_group_id):
        """Delete user groups from Keycloak."""
        # DELETE /{realm}/users/{id}/groups/{groupId}
        user_groups_endpoint = (
            provider_id.admin_user_endpoint
            + "/"
            + odoo_user.oauth_uid
            + "/groups/"
            + kc_group_id
        )
        logger.info("Calling DELETE %s" % user_groups_endpoint)
        headers = {
            "Authorization": "Bearer %s" % token,
        }
        resp = requests.delete(user_groups_endpoint, headers=headers)
        self._validate_response(resp, no_json=True)
        # yes, Keycloak sends back NOTHING on create
        # so we are forced to do another call to get its data :(
        return self._get_kc_user_groups(token, provider_id, odoo_user)

    def _assign_kc_user_groups(self):
        """Assing group to users on Keycloak.

        1. get a token
        2. check if _KC_CLIENT_AUTH_ACCESS_GROUP_ODOO is in KC groups
        3. assign or remove user group allow-odoo
        """
        provider_id = self.env.ref("energy_communities.keycloak_admin_provider")
        provider_id.validate_admin_provider()
        token = self._get_admin_token(provider_id)
        keycloak_groups = self._get_kc_groups(token, provider_id)
        group_name = [group["name"] for group in keycloak_groups]
        if not self._KC_CLIENT_AUTH_ACCESS_GROUP_ODOO in group_name:
            raise exceptions.UserError(_("User group odoo-allow doesn't exist."))
        else:
            group_id = "".join([group["id"] for group in keycloak_groups])
            for user in self:
                keycloak_user_groups = self._get_kc_user_groups(
                    token, provider_id, user
                )
                user_group_name = "".join(
                    group["name"] for group in keycloak_user_groups
                )
                if user.oauth_uid:
                    if (
                        user.get_user_auth_access_to_spaces()["odoo"]
                        and self._KC_CLIENT_AUTH_ACCESS_GROUP_ODOO != user_group_name
                    ):
                        # assign group odoo-allow
                        self._add_kc_user_groups(token, provider_id, user, group_id)
                    elif (
                        not user.get_user_auth_access_to_spaces()["odoo"]
                        and self._KC_CLIENT_AUTH_ACCESS_GROUP_ODOO == user_group_name
                    ):
                        # remove group odoo-allow
                        self._remove_kc_user_groups(token, provider_id, user, group_id)

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

    def _send_kc_reset_password_mail(self):
        provider_id = self.env.ref("energy_communities.keycloak_admin_provider")
        provider_id.validate_admin_provider()
        headers = {"Authorization": "Bearer %s" % self._get_admin_token(provider_id)}
        headers["Content-Type"] = "application/json"
        if provider_id.reset_password_endpoint:
            endpoint = provider_id.reset_password_endpoint.format(kc_uid=self.oauth_uid)
            response = requests.put(
                endpoint, headers=headers, data='["UPDATE_PASSWORD", "VERIFY_EMAIL"]'
            )
            self.write({"last_user_invitation_through_kc": datetime.now()})
        else:
            raise exceptions.UserError(_("Reset password url is not set."))
        if response.status_code != 204:
            raise exceptions.UserError(
                _(
                    "Something went wrong. Mail can not be sended. More details: {}"
                ).format(response.json())
            )

    def _update_kc_user_lang(self):
        provider_id = self.env.ref("energy_communities.keycloak_admin_provider")
        provider_id.validate_admin_provider()
        headers = {"Authorization": "Bearer %s" % self._get_admin_token(provider_id)}
        headers["Content-Type"] = "application/json"
        if provider_id.admin_user_endpoint:
            if self.oauth_uid:
                endpoint = provider_id.admin_user_endpoint + "/" + self.oauth_uid
                data = {
                    "attributes": {
                        "lang": [self.lang],
                    },
                }
                response = requests.put(endpoint, headers=headers, json=data)
                if response.status_code != 204:
                    raise exceptions.UserError(
                        _("Something went wrong. More details: {}").format(
                            response.json()
                        )
                    )
        else:
            raise exceptions.UserError(
                _("Keycloack provider admin user endpoint not defined")
            )

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

    def action_open_form_view(self):
        self.ensure_one()
        form_view = self.env.ref("base.view_users_form")
        return {
            "name": _("Users"),
            "res_model": "res.users",
            "res_id": self.id,
            "views": [
                (form_view.id, "form"),
            ],
            "type": "ir.actions.act_window",
            "target": "self",
        }
