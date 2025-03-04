from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"
    _name = "res.partner.bank"

    _sql_constraints = [
        (
            "unique_number",
            "unique(sanitized_acc_number, company_id, partner_id)",
            "Account Number must be unique",
        ),
    ]

    company_id = fields.Many2one(
        "res.company",
        "Company",
        related=False,
        readonly=False,
    )

    @api.constrains("partner_id")
    def _bank_account_company_id_not_null(self):
        for record in self:
            if not record.company_id:
                raise ValidationError("Company must be defined for ")
