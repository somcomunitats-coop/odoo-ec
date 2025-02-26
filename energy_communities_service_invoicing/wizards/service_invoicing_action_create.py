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
    service_invoicing_form_view_for_platform_admins,
    service_invoicing_tree_view,
)


class ServiceInvoicingActionCreateWizard(models.TransientModel):
    _name = "service.invoicing.action.create.wizard"
    _description = "Create service invoicing for an energy community"
    _inherit = ["user.currentcompany.mixin"]

    company_id = fields.Many2one("res.company", string="Coordinator")
    community_company_id = fields.Many2one(
        "res.company",
        string="Community",
        domain="[('id', 'in', allowed_community_company_ids)]",
    )
    community_company_mids = fields.Many2many(
        comodel_name="res.company",
    )
    service_pack_id = fields.Many2one(
        "product.product",
        string="Service pack",
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
        _compute="_compute_allowed_payment_mode_ids",
        store=False,
    )
    pack_product_categ_id = fields.Many2one(
        "product.category", compute="_compute_pack_product_categ_id", store=False
    )

    def _compute_pack_product_categ_id(self):
        for record in self:
            record.pack_product_categ_id = self.env.ref(
                "energy_communities_service_invoicing.product_category_pack"
            ).id

    @api.depends("company_id", "community_company_mids")
    def _compute_allowed_community_company_ids(self):
        for record in self:
            query = [("hierarchy_level", "=", "community")]
            if record.community_company_mids:
                query.append(("parent_id", "=", self.user_current_company.id))
            else:
                query.append(("parent_id", "=", record.company_id.id))
            record.allowed_community_company_ids = self.env["res.company"].search(query)

    @api.depends("company_id", "community_company_mids")
    def _compute_allowed_payment_mode_ids(self):
        for record in self:
            if record.community_company_mids:
                query = [("company_id", "=", self.user_current_company.id)]
            else:
                query = [("company_id", "=", record.company_id.id)]
            record.allowed_payment_mode_ids = self.env["account.payment.mode"].search(
                query
            )

    @api.onchange("company_id")
    def _compute_service_invoicing_action_create_wizard_allowed_values(self):
        for record in self:
            record._compute_allowed_community_company_ids()
            record._compute_allowed_payment_mode_ids()

    def execute_create(self):
        if self.community_company_mids:
            for community in self.community_company_mids:
                self._execute_create_one(
                    community,
                    community.parent_id,
                    self.env.company.service_invoicing_payment_mode_id,
                )
            return service_invoicing_tree_view(self.env)
        else:
            service_invoicing_id = self._execute_create_one(
                self.community_company_id, self.company_id, self.payment_mode_id
            )
            return service_invoicing_form_view_for_platform_admins(
                self.env, service_invoicing_id
            )

    def execute_create_one(self, community_company_id, company_id, payment_mode_id):
        self._validate_service_invoicing_action_create([community_company_id.id])
        existing_closed_contract = get_existing_last_closed_contract(
            self.env, company_id.partner_id, community_company_id
        )
        # If existing closed contract reopen it
        if existing_closed_contract:
            with contract_utils(self.env, existing_closed_contract) as component:
                service_invoicing_id = component.reopen(
                    datetime.now(),
                    self.pricelist_id,
                    self.service_pack_id,
                    self.discount,
                    payment_mode_id,
                )
        # If none of previous create a new contract
        else:
            with sale_order_utils(self.env) as component:
                service_invoicing_id = component.create_service_invoicing_initial(
                    company_id,
                    community_company_id,
                    self.service_pack_id,
                    self.pricelist_id,
                    payment_mode_id,
                    datetime.now(),
                    self.discount,
                    "activate",
                    "active_platform_service_invocing",
                )
        return service_invoicing_id

    def get_service_invoicing_action_create_wizard_form_view(self):
        if "active_ids" in self.env.context.keys():
            self._validate_service_invoicing_action_create(
                self.env.context["active_ids"]
            )
            self._validate_service_invoicing_action_create_multicommunity(
                self.env.context["active_ids"]
            )
            wizard = self.env["service.invoicing.action.create.wizard"].create(
                {
                    "community_company_mids": self.env.context["active_ids"],
                }
            )
            return {
                "type": "ir.actions.act_window",
                "res_model": "service.invoicing.action.create.wizard",
                "views": [
                    (
                        self.env.ref(
                            "energy_communities_service_invoicing.view_service_invoicing_action_create_wizard_form"
                        ).id,
                        "form",
                    ),
                ],
                "target": "new",
                "res_id": wizard.id,
            }
        return False

    def _validate_service_invoicing_action_create(self, company_id_list):
        impacted_records = self.env["res.company"].browse(company_id_list)
        # Check all selected companies are communities
        hierarchy_levels = list(set(impacted_records.mapped("hierarchy_level")))
        if len(hierarchy_levels) > 1 or hierarchy_levels[0] != "community":
            raise ValidationError(_("You can only assign pack to communities"))
        # Check if already open one and raise error
        for record in impacted_records:
            existing_contract = get_existing_open_contract(
                self.env, record.parent_id.partner_id, record
            )
            if existing_contract:
                raise_existing_same_open_contract_error(existing_contract)

    def _validate_service_invoicing_action_create_multicommunity(self, company_id_list):
        impacted_records = self.env["res.company"].browse(company_id_list)
        # check all communities have coordinator defined
        for record in impacted_records:
            if not record.parent_id:
                raise ValidationError(
                    _("Community {} must have a parent coordinator defined").format(
                        record.name
                    )
                )
        # Check current company has configuration payment mode for multicompany creation
        if (
            self.community_company_mids
            and not self.env.company.service_invoicing_payment_mode_id
        ):
            raise ValidationError(
                _(
                    "Platform {} must have a service invoicing payment mode defined"
                ).format(self.env.company.name)
            )
