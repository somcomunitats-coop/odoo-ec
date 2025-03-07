from odoo import api, fields, models

from ..utils import PACK_VALUES


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "pack.type.mixin"]

    ref_invoice_id = fields.Many2one(
        comodel_name="account.move",
        compute="_compute_ref_invoice_id_related_contract_id_is_contract",
        compute_sudo=True,
        store=False,
    )
    related_contract_id = fields.Many2one(
        comodel_name="contract.contract",
        compute="_compute_ref_invoice_id_related_contract_id_is_contract",
        compute_sudo=True,
        store=False,
    )
    is_contract = fields.Boolean(
        compute="_compute_ref_invoice_id_related_contract_id_is_contract",
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
    def _compute_ref_invoice_id_related_contract_id_is_contract(self):
        for record in self:
            record.ref_invoice_id = False
            record.related_contract_id = False
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
                    record.is_contract = rel_inv.is_contract
                    if rel_inv.related_contract_id:
                        record.related_contract_id = rel_inv.related_contract_id.id
            else:
                if record.invoice_line_ids:
                    first_move_line = record.invoice_line_ids[0]
                    if first_move_line.contract_line_id:
                        rel_contract = first_move_line.contract_line_id.contract_id
                        record.related_contract_id = rel_contract.id
                        record.is_contract = True

    def custom_compute_pack_type(self):
        self._set_custom_pack_type_on_invoice()

    @api.depends("ref", "invoice_line_ids")
    def _compute_pack_type(self):
        super()._compute_pack_type()

    # define configuration intercompany journal
    def _prepare_invoice_data(self, dest_company):
        inv_data = super()._prepare_invoice_data(dest_company)
        if (
            self.pack_type == "platform_pack"
            and dest_company.sudo().service_invoicing_purchase_journal_id
        ):
            inv_data[
                "journal_id"
            ] = dest_company.sudo().service_invoicing_purchase_journal_id.id
        return inv_data
