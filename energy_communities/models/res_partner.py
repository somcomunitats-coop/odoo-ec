import logging

from odoo import SUPERUSER_ID, api, fields, models

logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    gender = fields.Selection(
        selection_add=[
            ("not_binary", "Not binary"),
            ("not_share", "I prefer to not share it"),
        ]
    )

    @api.model
    def create(self, vals):
        current_company = self.env.company
        if self.env.user not in (
            self.env.ref("base.user_root"),
            self.env.ref("base.user_admin"),
        ):
            if vals.get("company_ids", False):
                vals["company_ids"][0][-1].append(current_company.id)

        new_partner = super().create(vals)
        return new_partner

    def cron_update_company_ids_from_user(self):
        partner_with_users = self.search(
            [("user_ids", "!=", False), ("user_ids.id", "!=", SUPERUSER_ID)]
        )
        for partner in partner_with_users:
            logger.info(
                "Updated company_ids to partner {}".format(partner.display_name)
            )
            if partner.user_ids.company_ids.ids:
                partner.write({"company_ids": partner.user_ids.company_ids.ids})
        self.env["res.users"].browse(SUPERUSER_ID).partner_id.write(
            {"company_ids": False}
        )

    def get_cooperator_from_vat(self, vat):
        if vat:
            vat = vat.strip()
        # email could be falsy or be only made of whitespace.
        if not vat:
            return self.browse()
        partner = self.search([("vat", "ilike", vat)], limit=1)
        return partner
