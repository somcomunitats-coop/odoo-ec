from odoo import api, fields, models


class MailComposeMessage(models.TransientModel):
    _name = "mail.compose.message"
    _inherit = "mail.compose.message"

    user_current_company = fields.Many2one(
        "res.company", compute="_compute_user_current_company", store=False
    )

    @api.depends("campaign_id")
    def _compute_user_current_company(self):
        for record in self:
            record.user_current_company = self.env.user.user_current_company

    @api.onchange("template_id")
    def _onchange_template_id_wrapper(self):
        self.ensure_one()
        if self.template_id.lang and "object.lang" in self.template_id.lang.lower():
            lang = self.env[self.model].browse(self.res_id).lang
            values = self.with_context(lang=lang)._onchange_template_id(
                self.template_id.id, self.composition_mode, self.model, self.res_id
            )["value"]
            for fname, value in values.items():
                setattr(self, fname, value)
        else:
            super()._onchange_template_id_wrapper()
