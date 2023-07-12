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


    def process_data(self):
        company_ids = self.env.context.get('active_ids')
        if not company_ids:
            raise ValidationError(_('Company not found'))

        company_id = company_ids[0]
        if self.is_new_admin:
            user = self.create_user(company_id)
        else:
            user = self.env['res.users'].search([('login', '=', self.vat)])


        company = self.env['res.company'].browse(company_id)
        company.add_ce_admin(user)
        user.make_internal_user()

        return True


    # TODO: Move this method inside res_users
    def create_user(self, company_id):
        vals = {
            "login": self.vat,
            "firstname": self.first_name,
            "lastname": self.last_name,
            "company_id": company_id,
            "company_ids": [(6, 0, [company_id])],
            "lang": self.lang.code,
            "email": self.email,
        }
        user = self.env["res.users"].create(vals)

        user.create_users_on_keycloak()
        user.send_reset_password_mail()


        return user
