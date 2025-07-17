from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import sale_order_utils


class SubscriptionRequest(models.Model):
    _name = "subscription.request"
    _inherit = "subscription.request"
    _description = "Subscription request"

    service_invoicing_sale_order_id = fields.Many2one(
        "sale.order", string="Service action (sale order)"
    )

    def validate_subscription_request(self):
        super().validate_subscription_request()
        if self.share_product_id.is_contract:
            # check pricelist is defined in order to create related service invoicing sale order
            if not self.company_id.pricelist_id:
                raise ValidationError(
                    "Your company has no Tariff associated. Please contact the platform administrator"
                )
            with sale_order_utils(self.env) as component:
                so_metadata = {
                    "company_id": self.company_id.id,
                }
                component.create_service_invoicing_sale_order(
                    self.partner_id,
                    self.share_product_id,
                    self.company_id.pricelist_id,
                    self.payment_mode_id,
                    fields.Date.today(),
                    "activate",
                    "validate_subscription_request_contract",
                    so_metadata,
                )
                self.write(
                    {"service_invoicing_sale_order_id": component.work.record.id}
                )
