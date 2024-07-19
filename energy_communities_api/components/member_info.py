from odoo.addons.component.core import Component

from ..schemas import MemberInfo


class MemberInfo(Component):
    _name = "member_info.service"
    _usage = "member_info.api"
    _collection = "energy_communities_member.components"

    def get_member_info(self, partner):
        member = partner.cooperative_membership_id
        return MemberInfo(
            email=partner.email,
            name=partner.name,
            lang=partner.lang,
            member_number=member.cooperator_register_number,
        )
