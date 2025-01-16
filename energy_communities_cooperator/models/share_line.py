from odoo import api, fields, models


class ShareLine(models.Model):
    _name = "share.line"
    _inherit = "share.line"
    _description = "Share line"

    share_product_id = fields.Many2one(readonly=False)
    share_unit_price = fields.Monetary(
        readonly=False,
    )
    related_invoice_line = fields.Many2one(
        "account.move.line", string="Related invoice line"
    )
    partner_id_id = fields.Integer(related="partner_id.id", store=False)
    company_id_id = fields.Integer(related="company_id.id", store=False)
    share_product_id_id = fields.Integer(related="share_product_id.id", store=False)

    @api.onchange("share_product_id")
    def _setup_share_unit_price(self):
        for record in self:
            record.share_unit_price = record.share_product_id.lst_price

    @api.onchange("share_unit_price", "share_number")
    def _setup_total_amount_line(self):
        for record in self:
            record.total_amount_line = record.share_unit_price * record.share_number

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}
