from odoo import fields, models
from odoo.tools.translate import _


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = ["res.company"]

    service_invoicing_sale_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Service invoicing sale journal",
    )
    service_invoicing_purchase_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Service invoicing purchase journal",
    )
    service_invoicing_sale_team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Service invoicing sales team",
    )
