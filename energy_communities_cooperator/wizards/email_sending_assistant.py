from odoo import _, api, fields, models


class EmailsendingassistantWiz(models.TransientModel):
    _name = "email.sending.assistant.wiz"
    _description = "Email Sending Assistant"

    num_selected_records = fields.Integer(
        string="Number of selected records",
        help="Number of selected records",
        default=lambda self: len(self.env.context.get("active_ids", [])),
    )

    def _get_domain_email_template(self):
        return [("model", "=", self.env.context.get("active_model"))]

    email_template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        help="Email template to send",
        domain=lambda self: self._get_domain_email_template(),
    )

    def _get_language_selection(self):
        langs = self.env["res.lang"].search([("active", "=", True)])
        return [(lang.code, lang.name) for lang in langs]

    force_language = fields.Selection(
        selection=lambda self: self._get_language_selection(),
        string="Force language",
        help="Language to send the email in",
    )

    recipient_email_address_for_test = fields.Char(
        string="Recipient email address for test",
        help="Email address to receive the test email",
    )

    state = fields.Selection(
        selection=[("draft", "Draft"), ("test", "Test")],
        string="State",
        default="draft",
    )

    def action_test_email(self):
        self.state = "test"
        ctx = self.env.context.copy() or {}
        return {
            "type": "ir.actions.act_window",
            "name": _("Send a test email"),
            "res_model": "email.sending.assistant.wiz",
            "view_mode": "form",
            "view_id": self.env.ref(
                "energy_communities_cooperator.email_sending_assistant_form_wizard"
            ).id,
            "target": "new",
            "context": ctx,
            "res_id": self.id,
        }

    def action_send_email(self):
        ctx = self.env.context.copy() or {}
        if self.force_language:
            template_force_language = self.email_template_id.copy(
                {"lang": self.force_language}
            )
        if self.state == "test":
            email_values = {
                "email_to": self.recipient_email_address_for_test,
            }
            if self.force_language:
                template_force_language.with_context(ctx).sudo().send_mail(
                    self.env.user.partner_id.id,
                    email_values=email_values,
                )
                template_force_language.unlink()
            else:
                self.email_template_id.with_context(ctx).sudo().send_mail(
                    self.env.user.partner_id.id,
                    email_values=email_values,
                )
            self.state = "draft"
            ctx = self.env.context.copy() or {}
            return {
                "type": "ir.actions.act_window",
                "name": _("Send email using existing template"),
                "res_model": "email.sending.assistant.wiz",
                "view_mode": "form",
                "view_id": self.env.ref(
                    "energy_communities_cooperator.email_sending_assistant_form_wizard"
                ).id,
                "context": ctx,
                "target": "new",
                "res_id": self.id,
            }
        else:
            if self.force_language:
                for id in ctx.get("active_ids"):
                    template_force_language.with_context(ctx).sudo().send_mail(id)
                template_force_language.unlink()
            else:
                for id in ctx.get("active_ids"):
                    self.email_template_id.with_context(ctx).sudo().send_mail(id)

    def action_cancel(self):
        if self.state == "test":
            self.state = "draft"
            ctx = self.env.context.copy() or {}
            return {
                "type": "ir.actions.act_window",
                "name": _("Send email using existing template"),
                "res_model": "email.sending.assistant.wiz",
                "view_mode": "form",
                "view_id": self.env.ref(
                    "energy_communities_cooperator.email_sending_assistant_form_wizard"
                ).id,
                "target": "new",
                "res_id": self.id,
                "context": ctx,
            }
