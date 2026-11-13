from lxml import etree

from odoo.tests import common
from odoo.tests.common import tagged


@tagged("-at_install", "post_install")
class TestShareProductActionGrouping(common.TransactionCase):
    def test_share_kanban_groups_by_contribution_category(self):
        action = self.env.ref("cooperator.product_template_action")
        search_view = self.env.ref(
            "energy_communities_cooperator.product_template_share_search_view"
        )

        self.assertEqual(action.search_view_id, search_view)
        self.assertIn("search_default_share_contribution_categ", action.context)
        self.assertIn('"default_is_share": True', action.context)

        arch = self.env["product.template"].get_view(search_view.id, "search")["arch"]
        group_by = etree.fromstring(arch).xpath(
            "//filter[@name='share_contribution_categ']"
        )
        self.assertEqual(len(group_by), 1)
        self.assertEqual(group_by[0].get("string"), "Contribution category")
        context = group_by[0].get("context").replace(" ", "")
        self.assertIn("'group_by':'categ_id'", context)
