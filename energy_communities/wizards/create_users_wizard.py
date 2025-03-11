from odoo import fields, models
from odoo.tools.translate import _

from ..utils import get_successful_popup_message, user_creator


class CreateUsersWizard(models.TransientModel):
    _name = "create.users.wizard"
    _description = "Create users Wizard"

    # TODO: refactor selection to get options from global res.users variable
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
        impacted_records = self.env[model].browse(self.env.context["active_ids"])
        role_id = self.env.ref("energy_communities.role_ce_member")
        with user_creator(self.env) as component:
            model = self.env.context.get("active_model")
            if model == "res.partner":
                component.create_users_from_cooperator_partners(
                    impacted_records, role_id, self.action, self.force_invite
                )
            if model == "res.company":
                component.create_users_from_communities_cooperator_partners(
                    impacted_records, role_id, self.action, self.force_invite
                )
        return get_successful_popup_message(
            _("User creation"), _("Process has been started.")
        )
