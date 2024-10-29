from odoo import api, fields, models
from odoo.tools.translate import _


class CmMap(models.Model):
    _inherit = "cm.map"

    admins_to_notify = fields.Many2many(
        "res.users", domain=[("role_line_ids.role_id.code", "=", "role_platform_admin")]
    )
