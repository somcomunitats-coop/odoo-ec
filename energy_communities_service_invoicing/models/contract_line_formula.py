from odoo import api, fields, models


class ContractLineFormula(models.Model):
    _name = "contract.line.qty.formula"
    _inherit = "contract.line.qty.formula"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=False
    )
