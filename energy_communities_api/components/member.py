from odoo.addons.component.core import Component


class MemberComponent(Component):
    _name = "member.component"
    _usage = "member.component"
    _collection = "energy_communities_member.api.services"

    def get_member_communities(self):
        print("AAAAAAA")
