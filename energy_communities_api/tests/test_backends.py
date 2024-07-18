from odoo.tests.common import TransactionCase

from ..backends import MemberInfoBackend


class TestMemberInfoBackend(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test__member_info_backend_isntance__ok(self):
        # if we create an instance of a member info backend
        member_info_backend = MemberInfoBackend()

        # then the instance is corretly created
        self.assertIsInstance(member_info_backend, MemberInfoBackend)
