import uuid

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestUserPreferences(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.instance = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")], limit=1
        )
        self.coordinator = self.env["res.company"].create(
            {
                "name": "Preferences Coordinator %s" % uuid.uuid4().hex[:8],
                "hierarchy_level": "coordinator",
                "parent_id": self.instance.id,
            }
        )
        self.community = self.env["res.company"].create(
            {
                "name": "Preferences Community %s" % uuid.uuid4().hex[:8],
                "hierarchy_level": "community",
                "parent_id": self.coordinator.id,
            }
        )
        self.other_community = self.env["res.company"].create(
            {
                "name": "Preferences Other Community %s" % uuid.uuid4().hex[:8],
                "hierarchy_level": "community",
                "parent_id": self.coordinator.id,
            }
        )
        self.member = self._create_user("Member")
        self._assign_role(self.member, "role_ce_member", self.community)
        self.platform_admin = self._create_user("Platform")
        self._assign_role(self.platform_admin, "role_platform_admin", self.instance)

    def _create_user(self, lastname):
        token = uuid.uuid4().hex[:8]
        return self.env["res.users"].create(
            {
                "firstname": "Preferences",
                "lastname": lastname,
                "login": "prefs-{}-{}".format(lastname.lower(), token),
                "email": "prefs-{}-{}@example.com".format(lastname.lower(), token),
            }
        )

    def _assign_role(self, user, role_code, company=None):
        vals = {
            "user_id": user.id,
            "role_id": self.env.ref("energy_communities.%s" % role_code).id,
        }
        if company:
            user.write({"company_ids": [(4, company.id)]})
            vals["company_id"] = company.id
        self.env["res.users.role.line"].create(vals)

    def test_hide_flag_follows_active_company_role(self):
        member_on_community = self.member.with_context(
            allowed_company_ids=[self.community.id]
        )
        member_on_other = self.member.with_context(
            allowed_company_ids=[self.other_community.id]
        )
        admin_on_instance = self.platform_admin.with_context(
            allowed_company_ids=[self.instance.id]
        )

        self.assertTrue(member_on_community.hide_advanced_user_preferences)
        self.assertFalse(member_on_other.hide_advanced_user_preferences)
        self.assertFalse(admin_on_instance.hide_advanced_user_preferences)

    def test_hidden_roles_and_platform_admin_depend_on_context(self):
        for role_code, company in (
            ("role_ce_admin", self.community),
            ("role_ce_manager", self.community),
            ("role_coord_admin", self.coordinator),
        ):
            user = self._create_user(role_code)
            self._assign_role(user, role_code, company)
            self._assign_role(user, "role_platform_admin", self.instance)
            self.assertTrue(
                user.with_context(
                    allowed_company_ids=[company.id]
                ).hide_advanced_user_preferences
            )
            self.assertFalse(
                user.with_context(
                    allowed_company_ids=[self.instance.id]
                ).hide_advanced_user_preferences
            )

    def test_member_without_admin_group_can_read_hide_flag(self):
        self._assign_role(self.member, "role_internal_user")
        self.member.with_context(
            allowed_company_ids=[self.community.id]
        ).set_groups_from_roles()
        self.env["res.users"].invalidate_model()

        self.assertFalse(self.member.has_group("energy_communities.group_admin"))
        self.assertFalse(self.member.has_group("base.group_erp_manager"))

        member_env = self.env(
            user=self.member.id,
            context={"allowed_company_ids": [self.community.id]},
        )
        with self.assertRaises(AccessError):
            member_env["res.users.role.line"].search([("user_id", "=", self.member.id)])

        member = member_env["res.users"].browse(self.member.id)
        self.assertTrue(member.hide_advanced_user_preferences)
        values = member.read(["hide_advanced_user_preferences"])
        self.assertTrue(values[0]["hide_advanced_user_preferences"])

    def test_active_company_ids_take_precedence(self):
        user = self.member.with_context(
            active_company_ids=[self.community.id],
            allowed_company_ids=[self.other_community.id],
        )
        self.assertTrue(user.hide_advanced_user_preferences)

    def test_preferences_view_hides_controls_only(self):
        preferences = self.env.ref("base.view_users_form_simple_modif")
        arch = etree.fromstring(preferences.get_combined_arch())
        hidden_nodes = {
            "notification_type": arch.xpath("//field[@name='notification_type']"),
            "odoobot_state": arch.xpath("//field[@name='odoobot_state']"),
            "technical_features": arch.xpath("//field[@name='technical_features']"),
            "api_keys": arch.xpath("//group[@name='auth']/following-sibling::group[1]"),
            "totp": arch.xpath(
                "//field[@name='totp_enabled']/following-sibling::div[1]"
            ),
        }
        for name, nodes in hidden_nodes.items():
            self.assertTrue(nodes, "%s is missing from preferences" % name)
            self.assertIn("hide_advanced_user_preferences", nodes[0].get("attrs"))
        self.assertEqual(hidden_nodes["api_keys"][0].get("string"), "API Keys")

        user_form = etree.fromstring(
            self.env.ref("base.view_users_form").get_combined_arch()
        )
        self.assertFalse(
            user_form.xpath("//field[@name='hide_advanced_user_preferences']")
        )
