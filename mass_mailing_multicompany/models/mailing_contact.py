from odoo import api, fields, models


class MassMailingContact(models.Model):
    _name = "mailing.contact"
    _inherit = "mailing.contact"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )

    @api.onchange("company_id")
    def _on_change_company_id(self):
        for record in self:
            # TODO: For being sure the contact belongs only to a contact of this company we would have to use company_id instead company_ids
            return {
                "domain": {
                    "partner_id": [("company_ids", "in", [record.company_id.id])]
                },
            }
