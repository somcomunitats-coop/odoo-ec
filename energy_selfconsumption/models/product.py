from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    project_id = fields.Many2one(
        "energy_project.project",
        required=True,
        ondelete="restrict",
        string="Energy Project",
        check_company=True,
    )
    contract_template_id = fields.Many2one("contract.template")
