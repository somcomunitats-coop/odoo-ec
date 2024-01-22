from odoo import api, fields, models


class MassMailing(models.Model):
    _name = "mailing.mailing"
    _inherit = ["mailing.mailing", "user.currentcompany.mixin"]

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )

    @api.depends("company_id")
    def _compute_user_current_company(self):
        super()._compute_user_current_company()

    @api.onchange("company_id")
    def _onchange_company_id(self):
        for record in self:
            record_user_current_company = record.get_user_current_company()
            return {
                "domain": {
                    "contact_list_ids": [
                        ("company_id", "=", record_user_current_company)
                    ],
                    "mail_server_id": [
                        ("company_id", "=", record_user_current_company)
                    ],
                    "campaign_id": [("company_id", "=", record_user_current_company)],
                }
            }
