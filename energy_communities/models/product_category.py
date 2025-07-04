from odoo import fields, models


class ProductCategory(models.Model):
    _name = "product.category"
    _inherit = "product.category"

    data_xml_id = fields.Char("XML ID")
