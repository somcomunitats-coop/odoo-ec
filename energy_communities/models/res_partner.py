from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gender = fields.Selection(selection_add=[("not_binary", "Not binary"),
                                             ("not_share", "I prefer to not share it")])
