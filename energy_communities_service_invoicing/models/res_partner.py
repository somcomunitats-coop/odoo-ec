from odoo import _, api, fields, models

from odoo.addons.energy_communities.config import PACK_TYPE_PLATFORM

from ..config import PACK_CONTRACT_STATUS_VALUES


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner"]

    platform_pack_id = fields.Many2one(
        "product.product",
        string="Platform Service Pack",
        compute="_compute_platform_pack_id",
        store=False,
    )
    platform_pack_contract_status = fields.Selection(
        selection=PACK_CONTRACT_STATUS_VALUES,
        string="Platform Service Pack Status",
        compute="_compute_platform_pack_status",
        store=False,
    )

    def _compute_platform_pack_status(self):
        for record in self:
            record.platform_pack_contract_status = "none"
            rel_contract = record._get_related_platform_pack_contract()
            if rel_contract:
                record.platform_pack_contract_status = rel_contract.status

    def _compute_platform_pack_id(self):
        for record in self:
            record.platform_pack_id = False
            rel_contract = record._get_related_platform_pack_contract()
            if rel_contract:
                if rel_contract.pack_id:
                    record.platform_pack_id = rel_contract.pack_id.id

    def _get_related_platform_pack_contract(self):
        return self.env["contract.contract"].search(
            [
                ("community_company_id", "=", self.related_company_id.id),
                ("pack_type", "=", PACK_TYPE_PLATFORM),
            ],
            limit=1,
        )
