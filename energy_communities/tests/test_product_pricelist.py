from odoo.exceptions import AccessError
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestProductPricelistAccess(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.ce_admin = cls._create_user_with_role("12345678Z", "role_ce_admin")
        cls.platform_admin = cls._create_user_with_role(
            "87654321X", "role_platform_admin"
        )
        cls.global_pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Global tariff",
                "company_id": False,
            }
        )
        cls.company_pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Company tariff",
                "company_id": cls.company.id,
            }
        )

    @classmethod
    def _create_user_with_role(cls, login, role_code):
        user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "firstname": "Tariff",
                    "lastname": login,
                    "login": login,
                    "email": "%s@example.com" % login,
                    "company_id": cls.company.id,
                    "company_ids": [(6, 0, [cls.company.id])],
                }
            )
        )
        role = cls.env["res.users.role"].search([("code", "=", role_code)], limit=1)
        cls.env["res.users.role.line"].create(
            {
                "user_id": user.id,
                "role_id": role.id,
                "company_id": cls.company.id,
            }
        )
        user.with_context(allowed_company_ids=[cls.company.id]).set_groups_from_roles()
        return user

    def _as_user(self, record, user):
        return record.with_user(user).with_context(
            allowed_company_ids=[self.company.id]
        )

    def test_tariffs_menu_is_visible_to_ce_roles(self):
        menu = self.env.ref("energy_communities.view_service_tariffs_menu")
        group_xmlids = [
            "energy_communities.role_platform_admin_res_groups",
            "energy_communities.role_coord_admin_res_groups",
            "energy_communities.role_ce_admin_res_groups",
            "energy_communities.role_ce_manager_res_groups",
        ]
        for xmlid in group_xmlids:
            self.assertIn(self.env.ref(xmlid), menu.groups_id)

    def test_company_id_defaults_to_context_company(self):
        defaults = self.env["product.pricelist"].default_get(
            ["name", "company_id", "currency_id"]
        )
        self.assertEqual(defaults["company_id"], self.company.id)

    def test_copy_assigns_context_company(self):
        copied = self.global_pricelist.copy()
        self.assertEqual(copied.company_id, self.company)

    def test_ce_admin_cannot_write_or_delete_global_pricelist(self):
        pricelist = self._as_user(self.global_pricelist, self.ce_admin)
        self.assertEqual(pricelist.name, "Global tariff")
        with self.assertRaises(AccessError):
            pricelist.write({"name": "Changed global tariff"})
        with self.assertRaises(AccessError):
            pricelist.unlink()

    def test_ce_admin_can_write_company_pricelist(self):
        pricelist = self._as_user(self.company_pricelist, self.ce_admin)
        pricelist.write({"name": "Company tariff updated"})
        self.assertEqual(pricelist.name, "Company tariff updated")

    def test_platform_admin_can_write_global_pricelist(self):
        pricelist = self._as_user(self.global_pricelist, self.platform_admin)
        pricelist.write({"name": "Global tariff updated"})
        self.assertEqual(pricelist.name, "Global tariff updated")
