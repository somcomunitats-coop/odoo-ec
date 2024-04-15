from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    product_categ_id = fields.Many2one(
        "product.category", compute="_compute_product_categ_id", store=True
    )

    @api.depends("invoice_line_ids")
    def _compute_product_categ_id(self):
        for record in self:
            if len(record.invoice_line_ids) == 1:
                record.product_categ_id = record.invoice_line_ids[
                    0
                ].product_id.categ_id.id
