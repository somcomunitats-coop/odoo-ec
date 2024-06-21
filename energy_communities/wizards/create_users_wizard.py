from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class CreateUsersWizard(models.TransientModel):
    _name = "create.users.wizard"
    _description = "Create users Wizard"

    create_user = fields.Boolean(
        string=_("Create Odoo user (in case it doesn't exist)")
    )
    create_kc_user = fields.Boolean(
        string=_("Create Keycloak user (in case it doesn't exist)")
    )
    invite_user_through_kc = fields.Boolean(
        string=_("Send invitation email to confirm email and reset password")
    )
    force_invite = fields.Boolean(
        string=_("Force send invitation email in case it wasn't sent")
    )

    def execute(self):
        if (
            not self.create_user
            or self.create_kc_user
            or self.invite_user_through_kc
            or self.force_invite
        ):
            raise ValidationError(_("Please select an action."))
        model = self.env.context.get("active_model")
        if model == "res.company":
            self.execute_on_company()
        elif model == "res.partner":
            self.execute_on_partner()

    def execute_on_company(self):
        if "active_ids" in self.env.context.keys():
            impacted_companies = self.env["res.company"].browse(
                self.env.context["active_ids"]
            )
            for company in impacted_companies:
                if company.hierarchy_level == "community":
                    coop = self.env["cooperative.membership"].search([])
                    partners = self.env["cooperative.membership"].search(
                        [
                            ("company_id", "=", company.id),
                            ("cooperator", "=", True),
                            ("member", "=", True),
                        ]
                    )
                    for partner in partners:
                        # self.env["res.users"].with_delay().build_platform_user(
                        self.env["res.users"].build_platform_user(
                            company,
                            partner.partner_id,
                            self.create_user,
                            self.create_kc_user,
                            self.invite_user_through_kc,
                            self.force_invite,
                            user_vals={},
                        )
                else:
                    raise ValidationError(
                        _("There is no company selected with level energy community.")
                    )

            return {
                "type": "ir.actions.act_window",
                "name": _("Wizard to generate users from partner members"),
                "res_model": "create.users.wizard",
                "view_type": "form",
                "view_mode": "form",
                "target": "new",
                "res_id": self.id,
            }

    def execute_on_partner(self):
        if "active_ids" in self.env.context.keys():
            partner = self.env["res.partner"].browse(self.env.context["active_id"])
            company = self.env["res.company"].search([("partner_id", "=", partner.id)])
            if len(company) > 1:
                raise ValidationError(
                    _(
                        "This wizard can only run with ONE company selected."
                        " Please limit the context of the selected companies to one."
                    )
                )
            else:
                if company.hierarchy_level == "community":
                    partners = self.env["cooperative.membership"].search(
                        [
                            ("company_id", "=", company.id),
                            ("cooperator", "=", True),
                            ("member", "=", True),
                        ]
                    )
                    for partner in partners:
                        self.env["res.users"].with_delay().build_platform_user(
                            company.id,
                            partner.partner_id,
                            self.create_user,
                            self.create_kc_user,
                            self.invite_user_through_kc,
                            self.force_invite,
                            user_vals={},
                        )
                else:
                    raise ValidationError(
                        _("There is no company selected with level energy community.")
                    )

            return {
                "type": "ir.actions.act_window",
                "name": _("Wizard to generate users from partner members"),
                "res_model": "create.users.wizard",
                "view_type": "form",
                "view_mode": "form",
                "target": "new",
                "res_id": self.id,
            }
