# Copyright 2017 LasLabs Inc.
# Copyright 2018 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = "sale.order"

    community_company_id = fields.Many2one(
        "res.company",
        string="Related community",
        domain="[('hierarchy_level','=','community')]",
    )

    def action_create_contract(self):
        contracts = super().action_create_contract()
        if self.community_company_id:
            for contract in contracts:
                contract.write(
                    {
                        "community_company_id": self.community_company_id.id,
                        "pricelist_id": self.pricelist_id.id,
                    }
                )
        return contracts
