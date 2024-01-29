from odoo import api, fields, models


class MassMailingContact(models.Model):
    _name = "mailing.contact"
    _inherit = ["mailing.contact", "user.currentcompany.mixin"]

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )

    @api.onchange("company_id")
    def _on_change_company_id(self):
        for record in self:
            return {
                "domain": {
                    "partner_id": [("company_ids", "in", [record.company_id.id])]
                },
            }

    def _set_partner(self):
        self.ensure_one()
        if not self.email:
            return
        m_partner = self.env["res.partner"]
        # Look for a partner with that email
        email = self.email.strip()
        partner = m_partner.search(
            [
                ("email", "=ilike", email),
                ("company_ids", "in", [self.env.user.get_current_company_id()]),
            ],
            limit=1,
        )
        if partner:
            # Partner found
            self.partner_id = partner
        else:
            lts = self.subscription_list_ids.mapped("list_id") | self.list_ids
            if lts.filtered("partner_mandatory"):
                # Create partner
                partner_vals = self._prepare_partner()
                self.partner_id = m_partner.sudo().create(partner_vals)

    def _prepare_partner(self):
        partner_vals = super()._prepare_partner()
        partner_vals["company_ids"] = [(4, self.env.user.get_current_company_id())]
        return partner_vals
