from odoo.tests.common import TransactionCase, tagged

from ..backends import MemberInfoBackend


@tagged("-at_install", "post_install")
class TestMemberInfoBackend(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test__get_member_info(self):
        # given a partner
        partner = self.env.ref("cooperator.res_partner_cooperator_1_demo")
        # given an isntance of a member info backend
        member_info_backend = MemberInfoBackend(self.env)

        # when we ask for the information of a member
        member_info = member_info_backend.get_member_info(partner)

        # then we have the information related whit that partner
        self.assertDictEqual(member_info.dict(), {})
        self.assertIsInstance(member_info_backend, MemberInfoBackend)
