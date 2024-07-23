from odoo.addons.component.core import Component

from ..schemas import CommunityInfo


class PartnerApiInfo(Component):
    _name = "partner.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "res.partner"

    def get_member_info(self, partner):
        return self.get(partner)

    def get_member_communities(self, partner):
        communities_ids = self._get_communities(partner)
        self.schema_class = CommunityInfo
        return self.get(communities_ids)

    def _get_communities(self, partner):
        return (
            self.env["cooperative.membership"]
            .search([("partner_id", "=", partner.id)])
            .mapped(lambda record: record.company_id.id)
        )
