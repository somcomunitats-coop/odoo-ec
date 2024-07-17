from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    selfconsumption_id = fields.One2many(
        "energy_selfconsumption.selfconsumption",
        related="contract_line_id.contract_id.project_id.selfconsumption_id",
    )


class AccountMove(models.Model):
    _inherit = "account.move"

    selfconsumption_invoicing_mode = fields.Selection(
        [
            ("none", "Empty"),
            ("power_acquired", "Power acquired"),
            ("energy_delivered", "Energy delivered"),
        ],
        compute="_compute_selfconsumption_invoicing_mode",
        store=False,
    )

    def _compute_selfconsumption_invoicing_mode(self):
        for record in self:
            if record.invoice_line_ids:
                if record.invoice_line_ids[0].selfconsumption_id:
                    record.selfconsumption_invoicing_mode = record.invoice_line_ids[
                        0
                    ].selfconsumption_id.invoicing_mode
                else:
                    record.selfconsumption_invoicing_mode = "none"
            else:
                record.selfconsumption_invoicing_mode = "none"
