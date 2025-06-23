from odoo import api, fields, models


class PackProductCreatorWizardServiceProduct(models.TransientModel):
    _name = "pack.product.creator.wizard.service.product"
    _description = "A service configuration included on a pack"

    name = fields.Char(string="Name")
    pack_product_creator_id = fields.Many2one("pack.product.creator.wizard")
    description_sale = fields.Text(string="Sales description")
    lst_price = fields.Float(
        "Service price",
        digits="Product Price",
    )
