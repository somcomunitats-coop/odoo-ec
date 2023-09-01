from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        check_company=True,
        domain="[('payment_type', '=', 'inbound')]",
    )
