from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    payment_date_equals_invoice_date = fields.Boolean(
        string="Payment Date = Invoice Date",
        default=False,
        help=(
            "When enabled, each selected invoice is paid using its own "
            "invoice date and payments are created separately."
        ),
    )

    def _create_payments(self):
        self.ensure_one()
        if self.payment_date_equals_invoice_date:
            # A payment has a single accounting date, so invoices cannot be grouped.
            self.group_payment = False
        return super()._create_payments()

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        return self._apply_invoice_date_as_payment_date(payment_vals, batch_result)

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        return self._apply_invoice_date_as_payment_date(payment_vals, batch_result)

    def _apply_invoice_date_as_payment_date(self, payment_vals, batch_result):
        if self.payment_date_equals_invoice_date:
            payment_vals["date"] = self._invoice_date_for_payment(batch_result)
        return payment_vals

    def _invoice_date_for_payment(self, batch_result):
        """Return the invoice date shared by every move in the payment batch."""
        self.ensure_one()
        moves = batch_result["lines"].move_id
        invoice_dates = set(moves.mapped("invoice_date"))
        invoice_date = next(iter(invoice_dates), False)
        if len(invoice_dates) == 1 and invoice_date:
            return invoice_date
        labels = ", ".join(moves.mapped("display_name"))
        raise UserError(
            _(
                "Each payment needs one invoice date. "
                "These entries have a missing or mixed invoice date: %s"
            )
            % labels
        )
