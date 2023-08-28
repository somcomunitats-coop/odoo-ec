from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    wordpress_base_url = fields.Char(
        related="company_id.wordpress_base_url",
        string=_("Wordpress Base URL (JWT auth)"),
        readonly=False,
    )
    """ WORDPRESS DB CREDENTIALS """
    wordpress_db_username = fields.Char(
        related="company_id.wordpress_db_username",
        string=_("Wordpress DB Admin Username"),
        readonly=False,
    )
    wordpress_db_password = fields.Char(
        related="company_id.wordpress_db_password",
        string=_("Wordpress DB Admin Password"),
        readonly=False,
    )
