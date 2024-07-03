from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class CreateUsersWizard(models.TransientModel):
    _name = "create.users.wizard"
    _description = "Create users Wizard"

    create_user = fields.Boolean(string="Create Odoo user (in case it doesn't exist)")
    create_kc_user = fields.Boolean(
        string="Create Keycloak user (in case it doesn't exist)"
    )
    invite_user_through_kc = fields.Boolean(
        string="Send invitation email to confirm email and reset password"
    )
    force_invite = fields.Boolean(
        string="Force send invitation email in case it wasn't sent"
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
        role_id = self.env.ref("energy_communities.role_ce_member")
        if model == "res.partner":
            if len(self.env.context["allowed_company_ids"]) > 1:
                raise ValidationError(
                    _(
                        "This wizard can only run with ONE company selected."
                        " Please limit the context of the selected companies to one."
                    )
                )
            else:
                company_id = self.env["res.company"].browse(
                    self.env.context["allowed_company_ids"]
                )
                partner_id = self.env["res.partner"].browse(
                    self.env.context["active_id"]
                )
                self.env["res.users"].build_platform_user(
                    company_id,
                    partner_id,
                    role_id,
                    self.create_user,
                    self.create_kc_user,
                    self.invite_user_through_kc,
                    self.force_invite,
                    user_vals={},
                )
        else:
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
                    for partner in partners:
                        self.env["res.users"].with_delay().build_platform_user(
                            company,
                            partner.partner_id,
                            role_id,
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
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "success",
                    "message": _("Process has been started."),
                    "sticky": False,
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }
