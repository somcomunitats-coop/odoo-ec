from asyncio.proactor_events import _ProactorBaseWritePipeTransport
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_sanitized_login_username(self):
        return ((self.vat and re.sub(r"[^a-zA-Z0-9]","",self.vat).lower()) or
            (self.name and re.sub(' +','_',re.sub(r"[^a-zA-Z0-9 ]","",self.name)).lower()))

    @api.multi
    def write(self, vals):
        result = super().write(vals)
        return result

    @api.multi
    def activate_partner_in_comunitat_energetica(self):
        """ Initialize all the specific 'Comunitats Energètiques' functionallity for this partner

        It assumes that the 'res_company.id' that belongs to this partner allready exist and it is the current active company of the uid, 
        and also the corresopondent Keycloak configuration amb entities related to it are allready set in KC (kc_realm/ck_client/kc_roles/kc_groups, etc).

        Tasks:
        1) Create the related Odoo res_user.
        2) Using the KC API create the related KC user:
            - Use as username the VAT number
            - By default assign the odoo role of 'CE Member'    
        3) WIP
        
        :return: (res.user) or raise Exception
        """
        self.ensure_one()
        user = self.create_user_from_partner_id()
        if user:
            self.user_id = user
            self.push_new_user_to_keyckoack()
        else: 
            raise UserError(_("Unable to create the new Odoo user related to this partner."))
        return user

    @api.multi
    def create_user_from_partner_id(self):
        """Create the related Odoo res_user:
            - Use the VAT number as 'login'
            - By default assign the odoo role of 'CE Member'

        :return: (res.users) the new user    
        """
        user_obj = self.env["res.users"]
        login = self._get_sanitized_login_username()

        user = user_obj.search([("login", "=", login)])
        #todo: add to the found existing user the actual company_id to company_ids in case actual company is not present

        if not user:
            user = user_obj.search(
                [("login", "=", login), ("active", "=", False)]
            )
            if user:
                user.sudo().write({"active": True})
                #todo: add to the found existing user the actual company_id to company_ids in case actual company is not present
            else:
                user = user_obj.sudo().with_context(no_reset_password=True)._signup_create_user(self._get_vals_for_create_user_from_partner_id())

        return user

    @api.multi
    def _get_vals_for_create_user_from_partner_id(self):

        self.ensure_one()
        res_users_o = self.env['res.users']
        ce_member_group_id = self.env['ir.model.data'].get_object_reference('ce','group_ce_member')[1]

        return {
            'email': self.email,
            'login': self._get_sanitized_login_username(),
            'partner_id': self.id,
            'company_id': self.company_id.id,
            'company_ids': [(6, 0, [self.company_id.id])],
            'groups_id': [(6,0,[9, ce_member_group_id])], # 9 = portal_user
        }

    @api.multi
    def push_new_user_to_keyckoack(self):
        self.ensure_one()
        return self.user_id.push_new_user_to_keyckoack()

    