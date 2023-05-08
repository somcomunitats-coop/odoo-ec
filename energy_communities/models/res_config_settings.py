# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ''' WORDPRESS DB CREDENTIALS '''
    wordpress_db_credentials_admin_username = fields.Char(
        related='company_id.wordpress_db_credentials_admin_username',
        string=_("Wordpress DB Admin Username"),
        readonly=False)
    wordpress_db_credentials_admin_password = fields.Char(
        related='company_id.wordpress_db_credentials_admin_password',
        string=_("Wordpress DB Admin Password"),
        readonly=False)

def get_wordpress_db_credentials(company):
    return {
        "admin_data": {
            "username": company.wordpress_db_credentials_admin_username,
            "password": company.wordpress_db_credentials_admin_password,
        }
    }