from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class AssignAdminWizard(models.TransientModel):
    _name = 'assign.admin.wizard'
    _description = 'Assign admin Wizard'

    is_new_admin = fields.Boolean(
        string=_("Is a new admin?")
    )
    first_name = fields.Char(string=_("First name"))
    last_name = fields.Char(string=_("Last name"))
    vat = fields.Char(string=_("VAT"))
    email = fields.Char(string=_("Email"))
    lang = fields.Many2one(
        'res.lang',
        string=_("Language")
    )
    role = fields.Selection(
        selection='_get_available_roles',
        string=_("Role")
    )

    @api.model
    def _get_available_roles(self):
        company = self.env['res.company'].browse(self.env.company.id)
        if company.hierarchy_level == 'community':
            return [
                ('role_ce_admin', _("Energy Community Administrator")),
                ('role_ce_member', _("Energy Community Member")),
            ]
        elif company.hierarchy_level == 'coordinator':
            return [  # TODO: branch_new_roles is required
                # ('role_ce_admin', _("Energy Community Administrator")),
                # ('role_ce_member', _("Energy Community Member"))
            ]
        return []

    def process_data(self):
        company_id = self.env.company.id
        if self.is_new_admin:
            user = self.env['res.users'].create_energy_community_user(
                vat=self.vat,
                first_name=self.first_name,
                last_name=self.last_name,
                lang_code=self.lang.code,
                email=self.email,
                company_id=company_id,
            )
        else:
            user = self.env['res.users'].search([('login', '=', self.vat)])

        user.add_energy_community_role(self.role, company_id)

        return True
