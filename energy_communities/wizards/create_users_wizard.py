from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class CreateUsersWizard(models.TransientModel):
    _name = "create.users.wizard"
    _description = "Create users Wizard"

    action = fields.Selection(
        [
            ("create_user", _("1) Create Odoo user (in case it doesn't exist)")),
            ("create_kc_user", _("2) Create Keycloak user (in case it doesn't exist)")),
            (
                "invite_user_through_kc",
                _("3) Send invitation email to confirm email and reset password"),
            ),
        ],
        default="create_user",
    )
    force_invite = fields.Boolean(
        string="Force send invitation email in case it has been already sent"
    )

    def execute(self):
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
                impacted_partners = self.env["res.partner"].browse(
                    self.env.context["active_ids"]
                )
                for partner in impacted_partners:
                    cooperator = self.env["cooperative.membership"].search(
                        [
                            ("partner_id", "=", partner.id),
                            ("company_id", "=", company_id.id),
                            ("cooperator", "=", True),
                            ("member", "=", True),
                        ]
                    )
                    if cooperator:
                        if len(impacted_partners) == 1:
                            self.env["res.users"].build_platform_user(
                                company_id,
                                partner,
                                role_id,
                                self.action,
                                self.force_invite,
                                user_vals={},
                            )
                        else:
                            self.env["res.users"].with_delay().build_platform_user(
                                company_id,
                                partner,
                                role_id,
                                self.action,
                                self.force_invite,
                                user_vals={},
                            )
        else:
            impacted_companies = self.env["res.company"].browse(
                self.env.context["active_ids"]
            )
            for company in impacted_companies:
                if company.hierarchy_level == "community":
                    cooperators = (
                        self.env["cooperative.membership"]
                        .sudo()
                        .search(
                            [
                                ("company_id", "=", company.id),
                                ("cooperator", "=", True),
                                ("member", "=", True),
                            ]
                        )
                    )
                    for cooperator in cooperators:
                        self.env["res.users"].with_delay().build_platform_user(
                            company,
                            cooperator.partner_id,
                            role_id,
                            self.action,
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
