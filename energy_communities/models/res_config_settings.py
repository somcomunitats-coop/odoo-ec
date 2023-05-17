# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ''' WORDPRESS DB CREDENTIALS '''
    wordpress_db_username = fields.Char(
        related='company_id.wordpress_db_username',
        string=_("Wordpress DB Username"),
        readonly=False)
    wordpress_db_password = fields.Char(
        related='company_id.wordpress_db_password',
        string=_("Wordpress DB Password"),
        readonly=False)

def get_wordpress_db_credentials(company):
    return {
        "data": {
            "username": company.wordpress_db_username,
            "password": company.wordpress_db_password,
        }
    }