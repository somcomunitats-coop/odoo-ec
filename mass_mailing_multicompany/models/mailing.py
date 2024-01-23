from odoo import api, fields, models


class MassMailing(models.Model):
    _name = "mailing.mailing"
    _inherit = ["mailing.mailing", "user.currentcompany.mixin"]

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )

    @api.depends("company_id")
    def _compute_user_current_company(self):
        super()._compute_user_current_company()

    @api.depends("company_id")
    def _compute_allowed_companies(self):
        super()._compute_allowed_companies()

    @api.onchange("company_id")
    def _onchange_company_id(self):
        for record in self:
            # record_user_current_company = record.get_user_current_company()
            return {
                "domain": {
                    "contact_list_ids": [("company_id", "=", record.company_id.id)],
                    "mail_server_id": [("company_id", "=", record.company_id.id)],
                    "campaign_id": [("company_id", "=", record.company_id.id)],
                }
            }
