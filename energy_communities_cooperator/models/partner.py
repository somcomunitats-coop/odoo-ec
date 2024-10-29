from odoo import _, api, fields, models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    gender = fields.Selection(
        selection_add=[
            ("not_binary", "Not binary"),
            ("not_share", "I prefer to not share it"),
        ]
    )
    company_register_number = fields.Char(
        string="Company Register Number",
        compute="_compute_company_register_number",
        store=True,
    )

    @api.depends("vat")
    def _compute_company_register_number(self):
        for record in self:
            if record.is_company:
                record.company_register_number = record.vat

    def _get_member_or_candidate_cooperative_membership(self, company_id):
        self.ensure_one()
        return (
            self.env["cooperative.membership"]
            .sudo()
            .search_count(
                [
                    "&",
                    "&",
                    ("partner_id", "=", self.id),
                    ("company_id", "=", company_id),
                    "|",
                    ("member", "=", True),
                    ("coop_candidate", "=", True),
                ]
            )
        )
