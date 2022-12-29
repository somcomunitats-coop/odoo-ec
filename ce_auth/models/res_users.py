from odoo import api, models, fields, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    def _generate_signup_values(self, provider, validation, params):
        """
        Overwrite method to get user values with user_id not email
        :param provider:
        :param validation:
        :param params:
        :return:
        """
        values = super(ResUsers, self)._generate_signup_values(provider, validation, params)
        values['login'] = validation['user_id']
        return values
