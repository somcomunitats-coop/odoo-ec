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
        [("draft", _("Draft")), ("posted", _("Posted")), ("sent", _("Sent"))],
        default="draft",
    )

    def action_post(self):
        for move in self.account_move_ids:
            if move.state == "draft":
                move.action_post()
        self.write({"state": "posted"})
        self.message_post(
            subject=_("Invoices successfully posted"),
            body=_("All voluntary share invoices has been successfully posted"),
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Invoices posted"),
                "message": _("Invoices successfully posted"),
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def action_send(self):
        for move in self.account_move_ids:
            if not self.partners_notified:
                self.with_delay()._send_voluntary_share_interest_return_email(move)
        self.write({"state": "sent", "partners_notified": True})
        self.message_post(
            subject=_("Invoices successfully sent"),
            body=_(
                "We have sent the voluntary share interest return document to related members via email."
            ),
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": _("Invoices sent"),
                "message": _(
                    "We have sent the voluntary share interest return document to related members via email."
                ),
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _send_voluntary_share_interest_return_email(self, move):
        self.company_id.get_voluntary_share_return_email_template().send_mail(
            force_send=False, res_id=move.id
        )
