from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    ref_invoice_id = fields.Many2one(
        comodel_name="account.move",
        compute="_compute_ref_invoice_id_related_contract_id_pack_type_is_contract",
        compute_sudo=True,
        store=False,
    )
    related_contract_id = fields.Many2one(
        comodel_name="contract.contract",
        compute="_compute_ref_invoice_id_related_contract_id_pack_type_is_contract",
        compute_sudo=True,
        store=False,
    )
    pack_type = fields.Boolean(
        compute="_compute_ref_invoice_id_related_contract_id_pack_type_is_contract",
        compute_sudo=True,
        store=True,
    )
    is_contract = fields.Boolean(
        compute="_compute_ref_invoice_id_related_contract_id_pack_type_is_contract",
        compute_sudo=True,
        store=True,
    )
    related_community_company_id = fields.Many2one(
        comodel_name="res.company",
        string="Related community",
        related="related_contract_id.community_company_id",
        domain="[('hierarchy_level','=','community')]",
    )

    @api.depends("invoice_line_ids", "ref")
    def _compute_ref_invoice_id_related_contract_id_pack_type_is_contract(self):
        for record in self:
            record.ref_invoice_id = False
            record.related_contract_id = False
            record.pack_type = 'none'
            record.is_contract = False
            rel_inv = False
            if record.ref:
                rel_inv = (
                    self.env["account.move"]
                    .sudo()
                    .search([("name", "=", record.ref)], limit=1)
                )
                if rel_inv:
                    record.ref_invoice_id = rel_inv.id
                    record.pack_type = rel_inv.pack_type
                    record.is_contract = rel_inv.is_contract
                    if rel_inv.related_contract_id:
                        record.related_contract_id = rel_inv.related_contract_id.id
            else:
                if record.invoice_line_ids:
                    first_move_line = record.invoice_line_ids[0]
                    if first_move_line.contract_line_id:
                        rel_contract = first_move_line.contract_line_id.contract_id
                        record.pack_type = rel_contract.pack_type
                        record.related_contract_id = rel_contract.id
                        record.is_contract = True
