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
    quantity = fields.Float(default=1.0, string="Quantity")
    qty_type = fields.Selection(
        selection=[("fixed", "Fixed quantity"), ("variable", "Variable quantity")],
        default="fixed",
        string="Quantity type",
    )
    qty_formula_id = fields.Many2one(
        comodel_name="contract.line.qty.formula", string="Quantity formula"
    )
    taxes_id = fields.Many2many(
        "account.tax",
        string="Customer Taxes",
        domain=[("type_tax_use", "=", "sale")],
    )
