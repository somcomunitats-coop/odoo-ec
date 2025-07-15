from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.energy_communities.config import PACK_TYPE_NONE


@tagged("-at_install", "post_install")
class TestPackTypeMixin(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_invoice_pack_type_case_0(self):
        # Given a demo invoice not pack generated
        invoice = self.env.ref("account.1_demo_invoice_3")
        self.assertEqual(invoice.pack_type, PACK_TYPE_NONE)

    def test_contract_pack_type_case_0(self):
        new_contract = self.env["contract.contract"].create(
            {
                "name": "Manual Test Contract",
                "partner_id": self.env.ref("base.res_partner_4").id,
                "journal_id": 1,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.assertEqual(new_contract.pack_type, PACK_TYPE_NONE)
