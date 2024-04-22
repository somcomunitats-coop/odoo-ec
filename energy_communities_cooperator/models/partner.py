from odoo import _, api, fields, models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

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
