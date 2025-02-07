from odoo import _, api, fields, models

from ..utils import _SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    community_company_id = fields.Many2one(
        "res.company",
        string="Related community",
        domain="[('hierarchy_level','=','community')]",
    )

    service_invoicing_action = fields.Selection(
        selection=_SALE_ORDER_SERVICE_INVOICING_ACTION_VALUES,
        required=True,
        string="Service invoicing action",
        default="none",
    )
    service_invoicing_modification_action = fields.Char(
        string="Modification action",
        default="none",
    )

    def action_create_contract(self):
        contracts = super().action_create_contract()
        if self.community_company_id:
            for contract in contracts:
                contract.write(
                    {
                        "community_company_id": self.community_company_id.id,
                        "pricelist_id": self.pricelist_id.id,
                        "payment_mode_id": self.payment_mode_id.id,
                    }
                )
        return contracts
