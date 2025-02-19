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

    company_id = fields.Many2one("res.company", string="Coordinator")
    community_company_id = fields.Many2one("res.company", string="Community")
    service_pack_id = fields.Many2one("product.product", string="Service pack")
    pricelist_id = fields.Many2one("product.pricelist", string="PriceList")
    payment_mode_id = fields.Many2one("account.payment.mode", string="Payment mode")
    discount = fields.Float(string="Discount (%)", digits="Discount", default=0)

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
                service_invoicing_id = (
                    component.create_service_invoicing_ready_to_start(
                        self.company_id,
                        self.community_company_id,
                        self.service_pack_id,
                        self.pricelist_id,
                        self.payment_mode_id,
                        datetime.now(),
                        self.discount,
                        "activate",
                    )
                )
        return service_invoicing_view(self.env, service_invoicing_id)
