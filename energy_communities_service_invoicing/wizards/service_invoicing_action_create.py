from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)

from ..utils import service_invoicing_view


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
        with sale_order_utils(self.env) as component:
            service_invoicing_id = component.create_service_invoicing_ready_to_start(
                self.company_id,
                self.community_company_id,
                self.service_pack_id,
                self.pricelist_id,
                self.payment_mode_id,
                datetime.now(),
                self.discount,
                "activate",
            )
        return service_invoicing_view(self.env, service_invoicing_id)
