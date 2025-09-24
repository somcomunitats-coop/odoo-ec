from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

from odoo.addons.energy_communities.config import (
    PACK_TYPE_NONE,
    PACK_TYPE_SELFCONSUMPTION,
)
from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)

from ..config import (
    INVOICE_MEMBERSHIP,
    INVOICE_OTHER,
    INVOICE_SELFCONSUMPTION,
    INVOICE_SERVICETYPE_LABELS,
)


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
    service_type = fields.Selection(
        selection=INVOICE_SERVICETYPE_LABELS,
        string="Service type of the invoice",
        compute="_compute_invoice_service_type",
        store=False,
    )

    @api.depends("pack_type", "company_id", "journal_id")
    def _compute_invoice_service_type(self):
        selfconsumption_journal = (
            self.env.ref("energy_selfconsumption.product_category_selfconsumption_pack")
            .with_company(self.company_id)
            .service_invoicing_sale_journal_id
        )
        for record in self:
            record.service_type = INVOICE_OTHER
            if record.journal_id == record.company_id.subscription_journal_id:
                record.service_type = INVOICE_MEMBERSHIP
            if (
                record.pack_type.lower() == PACK_TYPE_SELFCONSUMPTION
                or record.journal_id == selfconsumption_journal
            ):
                record.service_type = INVOICE_SELFCONSUMPTION

    @api.depends("invoice_line_ids")
    def _compute_pack_type(self):
        for record in self:
            record.pack_type = PACK_TYPE_NONE
            if record.invoice_line_ids:
                first_move_line = record.invoice_line_ids[0]
                if first_move_line.contract_line_id:
                    record.pack_type = (
                        first_move_line.contract_line_id.contract_id.pack_type
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

    def post_process_confirm_paid(self, effective_date):
        super().post_process_confirm_paid(effective_date)
        if self.subscription_request:
            subscriptions_sale_order = (
                self.subscription_request.service_invoicing_sale_order_id
            )
            if subscriptions_sale_order:
                # confirm sale order
                with sale_order_utils(self.env, subscriptions_sale_order) as component:
                    new_contract = component.confirm()
                # activate contract
                with contract_utils(self.env, new_contract) as component:
                    activation_date = self.payment_date
                    # Note: On contract activation when invoice payment we assume first iteration of contract is payed with the invoice
                    # So, recurring_next_date must be based on this assumption.
                    # On fixed yearly basis we add 1 year in order to move invoicing date one year.
                    fixed_invoicing_date_on_activation_date_year = date(
                        activation_date.year,
                        int(component.work.record.fixed_invoicing_month),
                        int(component.work.record.fixed_invoicing_day),
                    )
                    if component.work.record.recurring_rule_mode == "fixed":
                        activation_date = (
                            fixed_invoicing_date_on_activation_date_year
                            + relativedelta(years=+1)
                        )
                    component.activate(activation_date)
                # link contract to partners membership
                related_membership = self.partner_id.get_partner_membership_for_company(
                    self.company_id
                )
                if related_membership:
                    related_membership.write({"service_invoicing_id": new_contract.id})
        return True


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # Inter Company:
    # propagate name from origin invoice
    @api.model
    def _prepare_account_move_line(self, dest_move, dest_company):
        vals = super()._prepare_account_move_line(dest_move, dest_company)
        vals["name"] = self.name
        return vals
