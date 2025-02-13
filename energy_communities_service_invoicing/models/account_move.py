from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    ref_invoice_id = fields.Many2one(
        compute="_compute_ref_invoice_id_and_is_pack", store=False
    )
    is_pack = fields.Boolean(compute="_compute_ref_invoice_id_and_is_pack", store=True)

    @api.depends("invoice_line_ids", "ref")
    def _compute_ref_invoice_id_and_is_pack(self):
        for record in self:
            record.ref_invoice_id = False
            record.is_pack = False
            rel_inv = False
            if record.ref:
                rel_inv = (
                    self.env["account.move"]
                    .sudo()
                    .search([("name", "=", record.ref)], limit=1)
                )
                if rel_inv:
                    record.ref_invoice_id = rel_inv.id
                    record.is_pack = rel_inv.is_pack
            else:
                if record.invoice_line_ids:
                    first_move_line = record.invoice_line_ids[0]
                    if first_move_line.contract_line_id:
                        record.is_pack = (
                            first_move_line.contract_line_id.contract_id.is_pack
                        )
