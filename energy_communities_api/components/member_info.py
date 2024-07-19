from odoo import models

from odoo.addons.component.core import Component

from ..schemas import MemberInfo


class PartnerCollection(models.Model):
    _name = "res.partner.collection"
    _inherit = "collection.base"


class MemberInfoBackend(Component):
    _name = "member.info.backend"
    _usage = "member.info"
    _apply_on = "res.partner"
    _collection = "res.partner.collection"

    def get_member_info(self):
        pass
        # member = partner.cooperative_membership_id
        # return MemberInfo(
        #     email=partner.email,
        #     name=partner.name,
        #     lang=partner.lang,
        #     member_number=member.cooperator_register_number,
        # )
