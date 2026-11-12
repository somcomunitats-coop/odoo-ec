from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    payment_date_equals_invoice_date = fields.Boolean(
        string="Payment Date = Invoice Date and pay ordered by ascending invoice number",
        default=False,
        help=(
            "When enabled, each selected invoice is paid using its own "
            "invoice date. Payments are created separately and ordered by "
            "ascending invoice number."
        ),
    )

    def _create_payments(self):
        self.ensure_one()
        if self.payment_date_equals_invoice_date:
            # A payment has a single accounting date, so invoices cannot be grouped.
            self.group_payment = False
        return super()._create_payments()

    # OP#2187
    # This is because the invoices are grouped by partner and the partner invoices are sorted by invoice number.
    # If we don't sort the invoices by invoice number, the invoices will be paid in the wrong order.
    # This is because the invoices are grouped by partner and the partner invoices are sorted by invoice number.
    def _get_batches(self):
        batches = super()._get_batches()
        if not self.payment_date_equals_invoice_date:
            return batches
        if self.env.context.get("active_model") != "account.move":
            return batches

        def move_sort_key(line):
            return line.move_id.name or "", line.move_id.id

        def batch_sort_key(batch):
            return min(move_sort_key(line) for line in batch["lines"])

        # With separate payments, _create_payments() iterates each line. Restore
        # the invoice number order before it expands every batch into one payment
        # per move.
        if not self.group_payment:
            for batch in batches:
                batch["lines"] = batch["lines"].sorted(key=move_sort_key)

        return sorted(batches, key=batch_sort_key)

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
