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
        if "active_ids" in self.env.context.keys():
            impacted_companies = self.env["res.company"].browse(
                self.env.context["active_ids"]
            )
            for company in impacted_companies:
                if company.hierarchy_level == "community":
                    partners = self.env["cooperative.membership"].search(
                        [
                            ("company_id", "=", company.id),
                            ("cooperator", "=", True),
                            ("member", "=", True),
                        ]
                    )
                    for p in partners:
                        p.with_delay().build_platform_user(
                            company.id,
                            p.partner_id,
                            self.create_user,
                            self.create_kc_user,
                            self.invite_user_through_kc,
                            self.force_invite,
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
                "res_id": wizard.id,
            }
