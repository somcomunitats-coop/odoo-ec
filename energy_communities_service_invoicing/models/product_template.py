from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    property_contract_template_id = fields.Many2one(
        company_dependent=False,
    )
