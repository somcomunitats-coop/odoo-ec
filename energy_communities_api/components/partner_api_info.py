from odoo.addons.component.core import Component

from ..schemas import CommunityInfo
from ..utils import api_info


class PartnerApiInfo(Component):
    _name = "partner.api.info"
    _apply_on = "res.partner"
    _inherit = "api.info"

    def get_communities(self):
        self.recordset.ensure_one()
        record_ids = (
            self.env["cooperative.membership"]
            .search([("partner_id", "=", self.recordset.id)])
            .mapped(lambda record: record.company_id.id)
        )
        return api_info(
            self.env,
            CommunityInfo,
            "res.company",
            record_ids,
        ).get()
