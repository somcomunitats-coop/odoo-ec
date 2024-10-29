from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    contract_template_id = fields.Many2one("contract.template")
