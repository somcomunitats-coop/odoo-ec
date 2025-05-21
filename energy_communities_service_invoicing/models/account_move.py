from odoo import api, fields, models

from ..utils import PACK_VALUES


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "pack.type.mixin"]

    related_contract_id = fields.Many2one(
        comodel_name="contract.contract",
        compute="_compute_related_contract_id_is_contract",
        compute_sudo=True,
        store=True,
    )
    is_contract = fields.Boolean(
        compute="_compute_related_contract_id_is_contract",
        compute_sudo=True,
        store=True,
    )
    related_community_company_id = fields.Many2one(
        comodel_name="res.company",
        string="Related community",
        related="related_contract_id.community_company_id",
        domain="[('hierarchy_level','=','community')]",
        store=True,
    )

    @api.depends("invoice_line_ids", "auto_invoice_id")
    def _compute_related_contract_id_is_contract(self):
        for record in self:
            record.related_contract_id = False
            record.is_contract = False
            if record.auto_invoice_id:
                record.is_contract = record.auto_invoice_id.is_contract
                if record.auto_invoice_id.related_contract_id:
                    record.related_contract_id = (
                        record.auto_invoice_id.related_contract_id.id
                    )
            else:
                if record.invoice_line_ids:
                    first_move_line = record.invoice_line_ids[0]
                    if first_move_line.contract_line_id:
                        rel_contract = first_move_line.contract_line_id.contract_id
                        record.related_contract_id = rel_contract.id
                        record.is_contract = True

    @api.depends("invoice_line_ids", "auto_invoice_id")
    def _compute_pack_type(self):
        super()._compute_pack_type()

    def custom_compute_pack_type(self):
        self._set_custom_pack_type_on_invoice()

    # Inter Company:
    # define configuration journal
    def _prepare_invoice_data(self, dest_company):
        inv_data = super()._prepare_invoice_data(dest_company)
        if self.pack_type != "none":
            if self.related_contract_id:
                purchase_journal_id = (
                    self.related_contract_id.pack_id.categ_id.with_context(
                        company_id=dest_company.id
                    ).service_invoicing_purchase_journal_id
                )
                if purchase_journal_id:
                    inv_data["journal_id"] = purchase_journal_id.id
        return inv_data


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Inter Company:
    # propagate name from origin invoice
    @api.model
    def _prepare_account_move_line(self, dest_move, dest_company):
        vals = super()._prepare_account_move_line(dest_move, dest_company)
        vals["name"] = self.name
        return vals
