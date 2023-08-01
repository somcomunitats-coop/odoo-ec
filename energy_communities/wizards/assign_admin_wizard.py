from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class AssignAdminWizard(models.TransientModel):
    _name = 'assign.admin.wizard'
    _description = 'Assign admin Wizard'

    is_new_admin = fields.Boolean(string="Is a new admin?")
    first_name = fields.Char(string="First name")
    last_name = fields.Char(string="Last name")
    vat = fields.Char(string="VAT")
    email = fields.Char(string="Email")
    lang = fields.Many2one('res.lang', string="Language")
    role = fields.Selection(selection='_get_available_roles', string="Role")

    @api.model
    def _get_available_roles(self):
        company = self.env['res.company'].browse(self.env.company.id)
        if company.hierarchy_level == 'community':
            return [
                ('role_ce_admin', _("Energy Community Administrator")),
                ('role_ce_member', _("Energy Community Member")),
            ]
        elif company.hierarchy_level == 'coordinator':
            return [
                ('role_coord_admin', _("Coordinator Admin")),
                ('role_coord_worker', _("Coordinator Worker"))
            ]
        return []

    def process_data(self):
        if self.is_new_admin:
            user = self.env['res.users'].create_energy_community_base_user(
                vat=self.vat,
                first_name=self.first_name,
                last_name=self.last_name,
                lang_code=self.lang.code,
                email=self.email,
            )
        else:
            user = self.env['res.users'].search([
                ('login', 'ilike', self.vat)
            ], limit=1)
            if not user:
                raise ValidationError(_('User not found'))

        company_id = self.env.company.id
        user.add_energy_community_role(company_id, self.role)

        return True
