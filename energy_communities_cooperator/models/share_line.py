from odoo import api, fields, models


class ShareLine(models.Model):
    _name = "share.line"
    _inherit = "share.line"

    share_product_id = fields.Many2one(readonly=False)
