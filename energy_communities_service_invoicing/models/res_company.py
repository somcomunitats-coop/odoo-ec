from odoo import fields, models
from odoo.tools.translate import _


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    service_invoicing_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Service invoicing journal",
    )
