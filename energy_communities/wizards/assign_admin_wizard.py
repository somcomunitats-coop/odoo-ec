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
        if self.is_new_admin:
            user = self.create_user()
        else:
            user = self.env['res.users'].search([('login', '=', self.vat)])

        company_ids = self.env.context.get('active_ids')
        if not company_ids:
            raise ValidationError(_('Company not found'))
        company = self.env['res.company'].browse(company_ids[0])
        company.add_ce_admin(user)

        return True


    # TODO: Move this method inside res_users
    def create_user(self):
        vals = {
            "login": self.vat,
            "firstname": self.first_name,
            "lastname": self.last_name,
            "company_id": company_id,
            "company_ids": [company_id],
            "lang": self.lang.code,
            "email": self.email,
        }
        user = self.env["res.users"].create(vals)

        provider_id = self.env.ref('energy_communities.keycloak_admin_provider')
        provider_id.validate_admin_provider()
        token = self.env["res.users"]._get_admin_token(provider_id)

        keycloak_user = self.env["res.users"]._get_or_create_user(token, provider_id, user)
        keycloak_key = self.env["res.users"]._LOGIN_MATCH_KEY.split(':')[0]
        keycloak_login_provider = self.env.ref('energy_communities.keycloak_login_provider')
        user.update({
            'oauth_uid': keycloak_user[keycloak_key],
            'oauth_provider_id': keycloak_login_provider.id,
        })


        return user
