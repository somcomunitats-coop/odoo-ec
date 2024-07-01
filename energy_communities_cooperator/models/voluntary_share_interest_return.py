from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class VoluntaryShareInterestReturn(models.Model):
    _name = "voluntary.share.interest.return"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Name")
    start_date_period = fields.Date(string="Period start date")
    end_date_period = fields.Date(string="Period end date")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    account_move_ids = fields.One2many(
        "account.move", "voluntary_share_interest_return_id", string="Moves"
    )
    partners_notified = fields.Boolean(string="Partners notified")
    state = fields.Selection(
        [("draft", _("Draft")), ("posted", _("Posted")), ("completed", _("Completed"))],
        default="draft",
    )
    payment_order_id = fields.Many2one(
        "account.payment.order", string=_("Payment order")
    )

    def action_post(self):
        for move in self.account_move_ids:
            if move.state == "draft":
                move.action_post()
        self.write({"state": "posted"})
        return self._display_notifications(
            _("Invoices successfully posted"),
            _("We have posted the voluntary share interest return invoice documents"),
        )

    def action_send(self):
        for move in self.account_move_ids:
            if not self.partners_notified:
                self.with_delay()._send_voluntary_share_interest_return_email(move)
        self.write({"partners_notified": True})
        return self._display_notifications(
            _("Invoices successfully sent"),
            _(
                "We have sent the voluntary share interest return document to related members via email."
            ),
        )

    def action_complete(self):
        w_dict = {"state": "completed"}
        self.account_move_ids.create_account_payment_line()
        payment_order = self.env["account.payment.order"].search(
            [("state", "=", "draft"), ("company_id", "=", self.company_id.id)],
            order="id desc",
        )
        if payment_order:
            w_dict["payment_order_id"] = payment_order[0].id
        self.write(w_dict)
        return self._display_notifications(
            _("Payment order generated"),
            _("We have generated the payment order in order to return the interests."),
        )

    def _send_voluntary_share_interest_return_email(self, move):
        self.company_id.get_voluntary_share_return_email_template().send_mail(
            force_send=False, res_id=move.id
        )

    def _display_notifications(self, subject, body):
        self.message_post(
            subject=subject,
            body=body,
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": subject,
                "message": body,
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
