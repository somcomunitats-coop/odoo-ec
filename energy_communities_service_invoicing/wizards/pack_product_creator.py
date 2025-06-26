from odoo import api, fields, models

from odoo.addons.energy_communities.utils import product_utils


class PackProductCreatorWizard(models.TransientModel):
    _name = "pack.product.creator.wizard"
    _inherit = ["contract.recurrency.basic.mixin"]
    _description = "Assistant for creating a pack product complete configuration"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    pack_categ_id = fields.Many2one("product.category", string="Pack category")
    name = fields.Char(string="Pack name")
    description_sale = fields.Text(string="Sales description")
    list_price = fields.Float(
        "Pack activation price",
        digits="Product Price",
    )
    taxes_id = fields.Many2many(
        "account.tax",
        string="Customer Taxes",
        domain=[("type_tax_use", "=", "sale")],
    )
    service_product_ids = fields.One2many(
        "pack.product.creator.wizard.service.product",
        "pack_product_creator_id",
        string="Included services",
    )

    def execute_create(self):
        with product_utils(self.env) as component:
            component.create_products()
