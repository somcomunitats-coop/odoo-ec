from odoo import fields, models


class UtmSource(models.Model):
    _inherit = "utm.source"

    source_ext_id = fields.Char("ID Ext Source")
