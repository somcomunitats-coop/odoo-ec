from odoo import api, fields, models


class MassMailing(models.Model):
    _name = "mailing.mailing"
    _inherit = ["mailing.mailing", "user.currentcompany.mixin"]

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )

    @api.onchange("company_id")
    def _onchange_company_id(self):
        for record in self:
            return {
                "domain": {
                    "contact_list_ids": [("company_id", "=", record.company_id.id)],
                    "mail_server_id": [("company_id", "=", record.company_id.id)],
                    "campaign_id": [("company_id", "=", record.company_id.id)],
                }
            }

    def _get_default_mailing_domain(self):
        mailing_domain = super()._get_default_mailing_domain()
        if self.mailing_model_real == "res.partner":
            mailing_domain.append(
                ("company_ids", "in", [self.env.user.get_current_company_id()])
            )
        else:  # crm.lead, mailing.contact, sale.order, mailing.contact
            mailing_domain.append(
                ("company_id", "=", self.env.user.get_current_company_id())
            )
        return mailing_domain
