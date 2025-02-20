from odoo import api, fields, models


class ContractLine(models.Model):
    _inherit = "contract.line"

    ordered_qty_type = fields.Char()
    ordered_quantity = fields.Float()
    ordered_qty_formula_id = fields.Many2one("contract.line.qty.formula")

    def _compute_allowed(self):
        super()._compute_allowed()
        for record in self:
            record.is_cancel_allowed = True
