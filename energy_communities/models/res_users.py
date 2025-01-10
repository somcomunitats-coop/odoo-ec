import logging
import re
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
            self.env.ref("energy_communities.role_coord_worker"),
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

        company_ids = self.env.context.get("active_company_ids") or self.company_id.ids
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
            "role_coord_worker",
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

    # TODO: Delete this method when deleting unused services using it.
    # TODO: Modify this method to make it compatible with currentuser mixin
    def get_role_codes(self):
        # TODO Map all code to company and enable (We should update the API schema too)
        return self.role_line_ids[0].role_id.code

    # TODO: Check how this is compatible with new role refactors.
    def get_related_company_role(self, company_id, role_codes=False):
        if role_codes:
            current_role_lines = self.role_line_ids.filtered(
                lambda role_line: role_line.company_id.id == company_id
                and role_line.role_id.code in role_codes
            )
        else:
            current_role_lines = self.role_line_ids.filtered(
                lambda role_line: role_line.company_id.id == company_id
            )
        return current_role_lines

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

    def make_coord_user(self, company_id, role_name):
        # create ce user on this company
        self.make_ce_user(company_id, role_name)
        # apply manager role the child companies
        company = self.env["res.company"].browse(company_id)
        child_companies = company.get_child_companies()
        for child_company in child_companies:
            self.make_ce_user(child_company.id, "role_ce_manager")

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
    # TODO: New keycloak_utils component created going to be used on registration.
    # record = self.env["res.users"].browse(18)
    # with keycloak_utils(self.env,record) as component:
    #     model = self.env.context.get("active_model")
    #     component.foo()
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
