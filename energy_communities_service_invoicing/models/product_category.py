from odoo import _, api, fields, models


class ProductCategory(models.Model):
    _name = "product.category"
    _inherit = "product.category"

    service_invoicing_sale_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Service invoicing sale journal",
        company_dependent=True,
        help="This journal will be used when creating service invoicing contracts",
    )
    service_invoicing_purchase_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Service invoicing purchase journal",
        company_dependent=True,
        help="This journal will be used when creating service invoicing contracts",
    )
    service_invoicing_sale_team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Service invoicing sales team",
        company_dependent=True,
        help="This sale team will be used when creating service invoicing sale orders",
    )
