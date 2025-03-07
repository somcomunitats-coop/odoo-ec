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
        required=True,
        default=lambda self: self.env.company,
        domain="[('id','in',allowed_company_ids)]",
    )

    allowed_company_ids = fields.Many2many(
        comodel_name="res.company",
        compute="_compute_allowed_company_ids",
        store=False,
    )

    @api.constrains("partner_id")
    def _bank_account_company_id_not_null(self):
        for record in self:
            if not record.company_id:
                raise ValidationError("Company must be defined for ")

    @api.depends("partner_id")
    def _compute_allowed_company_ids(self):
        for record in self:
            record.allowed_company_ids = record._get_partner_company_ids()

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        for record in self:
            record.allowed_company_ids = record._get_partner_company_ids()

    def _get_partner_company_ids(self):
        return self.partner_id.company_ids
