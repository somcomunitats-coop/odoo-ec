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

    # skip last_date_invoice update for modification action if contract is ready to start or on free plan.
    def _update_recurring_next_date(self):
        # TODO: Pay attention to original code in order to detect if method has been renamed:
        # FIXME: Change method name according to real updated field
        # e.g.: _update_last_date_invoiced()
        for record in self:
            if record.contract_id.status == "paused" or record.contract_id.is_free_pack:
                return
        super()._update_recurring_next_date()

    def _set_name(self, data):
        name = self.name
        for key, value in data.items():
            name = name.replace(f"#{key}#", str(value))
        self.write({"name": name})
