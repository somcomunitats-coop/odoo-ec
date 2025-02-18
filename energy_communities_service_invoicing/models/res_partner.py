from odoo import _, api, fields, models

from ..utils import _CONTRACT_STATUS_VALUES

_PACK_CONTRACT_STATUS_VALUES = _CONTRACT_STATUS_VALUES + [("none", _("None"))]


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner"]

    service_pack_id = fields.Many2one(
        "product.product",
        string="Service Pack",
        compute="_compute_service_pack_id",
        store=False,
    )
    pack_contract_status = fields.Selection(
        selection=_PACK_CONTRACT_STATUS_VALUES,
        string="Service Pack Status",
        compute="_compute_service_pack_status",
        store=False,
    )

    def _compute_service_pack_status(self):
        for record in self:
            record.pack_contract_status = "none"
            rel_contract = record._get_related_service_contract()
            if rel_contract:
                record.pack_contract_status = rel_contract.status

    def _compute_service_pack_id(self):
        for record in self:
            record.service_pack_id = False
            rel_contract = record._get_related_service_contract()
            if rel_contract:
                if rel_contract.service_pack_id:
                    record.service_pack_id = rel_contract.service_pack_id.id

    def _get_related_service_contract(self):
        return self.env["contract.contract"].search(
            [
                ("community_company_id", "=", self.related_company_id.id),
                ("is_pack", "=", True),
            ],
            limit=1,
        )
