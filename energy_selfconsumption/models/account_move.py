from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    selfconsumption_id = fields.One2many(
        "energy_selfconsumption.selfconsumption",
        related="contract_line_id.contract_id.project_id.selfconsumption_id",
    )


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_name_invoice_report(self):
        self.ensure_one()
        if (
            self.invoice_line_ids.selfconsumption_id.invoicing_mode
            == "energy_delivered"
        ):
            return "energy_selfconsumption.energy_delivered_invoice_template"
        elif (
            self.invoice_line_ids.selfconsumption_id.invoicing_mode == "power_acquired"
        ):
            return "energy_selfconsumption.power_acquired_invoice_template"
        return super()._get_name_invoice_report()
