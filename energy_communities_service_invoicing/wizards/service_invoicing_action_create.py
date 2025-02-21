from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)

from ..utils import (
    get_existing_last_closed_contract,
    get_existing_open_contract,
    raise_existing_same_open_contract_error,
    service_invoicing_view,
)


class ServiceInvoicingActionCreateWizard(models.TransientModel):
    _name = "service.invoicing.action.create.wizard"
    _description = "Create service invoicing for an energy community"
    _inherit = ["user.currentcompany.mixin", "service.invoicing.info.mixin"]

    company_id = fields.Many2one("res.company", string="Coordinator")
    community_company_id = fields.Many2one(
        "res.company",
        string="Community",
        domain="[('id', 'in', allowed_community_company_ids)]",
    )
    service_pack_id = fields.Many2one(
        "product.product",
        string="Service pack",
        domain="[('id', 'in', pack_product_product_ids)]",
        precompute=True,
    )
    payment_mode_id = fields.Many2one(
        "account.payment.mode",
        string="Payment mode",
        domain="[('id', 'in', allowed_payment_mode_ids)]",
    )
    pricelist_id = fields.Many2one("product.pricelist", string="PriceList")
    discount = fields.Float(string="Discount (%)", digits="Discount", default=0)

    allowed_community_company_ids = fields.Many2many(
        comodel_name="res.company",
        _compute="_compute_allowed_community_company_ids",
        store=False,
    )
    allowed_payment_mode_ids = fields.Many2many(
        comodel_name="account.payment.mode",
        _compute="_compute_ allowed_payment_mode_ids",
        store=False,
    )

    @api.depends("company_id")
    def _compute_allowed_community_company_ids(self):
        for record in self:
            record.allowed_community_company_ids = self.env["res.company"].search(
                [
                    ("hierarchy_level", "=", "community"),
                    ("parent_id", "=", record.company_id.id),
                ]
            )

    def _compute_allowed_payment_mode_ids(self):
        for record in self:
            record.allowed_payment_mode_ids = self.env["account.payment.mode"].search(
                [("company_id", "=", self.user_current_company.id)]
            )

    @api.onchange("company_id")
    def _on_change_company_id(self):
        for record in self:
            record._compute_allowed_community_company_ids()
            record._compute_allowed_payment_mode_ids()
            # TODO: This should be necessary if pack_product_product_ids gets properly auto computed
            record._compute_pack_product_product_ids()

    def execute_create(self):
        # Check if already open one and raise error
        existing_contract = get_existing_open_contract(
            self.env, self.company_id.partner_id, self.community_company_id
        )
        if existing_contract:
            raise_existing_same_open_contract_error()
        existing_closed_contract = get_existing_last_closed_contract(
            self.env, self.company_id.partner_id, self.community_company_id
        )
        # If existing closed contract reopen it
        if existing_closed_contract:
            with contract_utils(self.env, existing_closed_contract) as component:
                service_invoicing_id = component.reopen(
                    datetime.now(),
                    self.pricelist_id,
                    self.service_pack_id,
                    self.discount,
                    self.payment_mode_id,
                )
        # If none of previous create a new contract
        else:
            with sale_order_utils(self.env) as component:
                service_invoicing_id = component.create_service_invoicing_initial(
                    self.company_id,
                    self.community_company_id,
                    self.service_pack_id,
                    self.pricelist_id,
                    self.payment_mode_id,
                    datetime.now(),
                    self.discount,
                    "activate",
                    "active_platform_service_invocing",
                )
        return service_invoicing_view(self.env, service_invoicing_id)
