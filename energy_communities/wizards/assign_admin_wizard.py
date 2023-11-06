import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class AssignAdminWizard(models.TransientModel):
    _name = "assign.admin.wizard"
    _description = "Assign admin Wizard"

    is_new_admin = fields.Boolean(string="Is a new admin?")
    first_name = fields.Char(string="First name", required=True)
    last_name = fields.Char(string="Last name", required=True)
    vat = fields.Char(string="VAT", required=True)
    email = fields.Char(string="Email", required=True)
    lang = fields.Many2one("res.lang", string="Language", required=True)
    role = fields.Selection(
        selection="_get_available_roles", string="Role", required=True
    )
    user_is_coordinator_worker = fields.Boolean(compute="_user_is_coordinator_worker")

    def _user_is_coordinator_worker(self):
        for record in self:
            role = self.env.ref("energy_communities.role_coord_worker")
            role_line = self.env["res.users.role.line"].search(
                [("user_id", "=", self.env.user.id), ("role_id", "=", role.id)], limit=1
            )
            record.user_is_coordinator_worker = bool(role_line)

    @api.model
    def _get_available_roles(self):
        company = self.env.company
        if company.hierarchy_level == "community":
            return [
                ("role_ce_admin", _("Energy Community Administrator")),
                ("role_ce_member", _("Energy Community Member")),
            ]
        elif company.hierarchy_level == "coordinator":
            return [
                ("role_coord_admin", _("Coordinator Admin")),
                ("role_coord_worker", _("Coordinator Worker")),
            ]
        elif company.hierarchy_level == "instance":
            return [
                ("role_coord_admin", _("Coordinator Admin")),
                ("role_coord_worker", _("Coordinator Worker")),
                ("role_ce_admin", _("Energy Community Administrator")),
                ("role_ce_member", _("Energy Community Member")),
            ]
        return []

    def process_data(self):
        vat = re.sub(r"[^a-zA-Z0-9]", "", self.vat).upper()
        if self.is_new_admin:
            user = self.env["res.users"].create_energy_community_base_user(
                vat=vat,
                first_name=self.first_name,
                last_name=self.last_name,
                lang_code=self.lang.code,
                email=self.email,
            )
        else:
            user = self.env["res.users"].search([("login", "ilike", vat)], limit=1)
            if not user:
                raise ValidationError(_("User not found"))

        company_id = self.env.company.id
        if self.user_is_coordinator_worker:
            raise ValidationError(
                _(
                    "Since you are not a coordinator admin you are not allowed to assign coordinator admins."
                )
            )
        else:
            user.add_energy_community_role(company_id, self.role)
        return True
