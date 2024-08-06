from odoo.addons.base.models.res_partner import Partner
from odoo.addons.component.core import Component

from ..schemas import CommunityInfo, MemberInfo


class PartnerApiInfo(Component):
    _name = "partner.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "res.partner"

    def get_member_info(self, partner: Partner) -> MemberInfo:
        return self.get(partner)

    def total_member_communities(self, partner: Partner) -> int:
        return self.env["cooperative.membership"].search_count(
            [("partner_id", "=", partner.id)]
        )

    def get_member_communities(
        self,
        partner: Partner,
    ) -> CommunityInfo:
        communities = self._get_communities(partner)
        if communities:
            return self.get_list(communities)
        return []

    def _get_communities(self, partner: Partner):
        if self.work.paging:
            return (
                self.env["cooperative.membership"]
                .search(
                    [("partner_id", "=", partner.id)],
                    limit=self.work.paging.limit,
                    offset=self.work.paging.offset,
                )
                .mapped(lambda record: record.company_id)
            )
        return (
            self.env["cooperative.membership"]
            .search([("partner_id", "=", partner.id)])
            .mapped(lambda record: record.company_id)
        )
