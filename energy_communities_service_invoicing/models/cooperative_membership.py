from odoo import fields, models


class CooperativeMembership(models.Model):
    _name = "cooperative.membership"
    _inherit = "cooperative.membership"

    service_invoicing_id = fields.Many2one(
        "contract.contract", string="Related contract"
    )
