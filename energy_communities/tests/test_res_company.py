from unittest import skip

from odoo.exceptions import ValidationError
from odoo.tests import common

from .helpers import CompanySetupMixin, UserSetupMixin


class TestResCompany(CompanySetupMixin, UserSetupMixin, common.TransactionCase):
    def test_hierarchy_level_company_instance(self):
        company_instance = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        if not company_instance:
            company_instance = self.env["res.company"].create(
                {"name": "Instance Company", "hierarchy_level": "instance"}
            )
        self.assertEqual(company_instance.hierarchy_level, "instance")

        company_instance_count = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        self.assertEqual(len(company_instance_count), 1)

        self.assertEqual(company_instance.parent_id, self.env["res.company"])

        with self.assertRaises(ValidationError):
            self.env["res.company"].create(
                {"name": "Instance Company Error", "hierarchy_level": "instance"}
            )

    def test_hierarchy_level_company_coordinator(self):
        company_instance = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        company_coordinator = self.env["res.company"].create(
            {
                "name": "Coordinator Company",
                "hierarchy_level": "coordinator",
                "parent_id": company_instance.id,
            }
        )
        self.assertEqual(company_coordinator.hierarchy_level, "coordinator")
        self.assertEqual(company_coordinator.parent_id.hierarchy_level, "instance")
        self.assertEqual(company_coordinator.parent_id_filtered_ids, company_instance)

        company_community = self.env["res.company"].create(
            {
                "name": "Community Company Test",
                "hierarchy_level": "community",
                "parent_id": company_coordinator.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["res.company"].create(
                {
                    "name": "coordinator Company",
                    "hierarchy_level": "coordinator",
                    "parent_id": company_community.id,
                }
            )

    def test_hierarchy_level_company_community(self):
        company_coordinator = self.env["res.company"].search(
            [("hierarchy_level", "=", "coordinator")], limit=1
        )
        company_community = self.env["res.company"].create(
            {
                "name": "Community Company",
                "hierarchy_level": "community",
                "parent_id": company_coordinator.id,
            }
        )
        self.assertEqual(company_community.hierarchy_level, "community")
        self.assertEqual(company_community.parent_id.hierarchy_level, "coordinator")
        all_company_coordinator = self.env["res.company"].search(
            [("hierarchy_level", "=", "coordinator")]
        )
        self.assertEqual(
            company_community.parent_id_filtered_ids, all_company_coordinator
        )

        company_instance = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        with self.assertRaises(ValidationError):
            self.env["res.company"].create(
                {
                    "name": "Community Company Error",
                    "hierarchy_level": "community",
                    "parent_id": company_instance.id,
                }
            )
        with self.assertRaises(ValidationError):
            self.env["res.company"].create(
                {
                    "name": "Community Company Error 2",
                    "hierarchy_level": "community",
                    "parent_id": company_community.id,
                }
            )

    @skip(
        "This test is not stable and consistent, until we understand what want to test, we will skip it"
    )
    def test__get_users__without_roles(self):
        # Given a coord company and coord admin
        company_instance = self.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        company_coordinator = self.create_company(
            "Som", "coordinator", company_instance.id
        )
        user = self.create_user("Tom", "Bombadil")
        self.make_coord_admin(company_coordinator, user)

        # When we want all users of company_coordinator
        community_users = company_coordinator.get_users()

        # Then returns all community users
        platform_admins = (
            self.env["res.users.role.line"]
            .search(
                [
                    (
                        "role_id",
                        "=",
                        self.env.ref("energy_communities.role_platform_admin").id,
                    ),
                ]
            )
            .user_id
        )
        self.assertEqual(community_users, user + platform_admins)
