# from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.base.models.ir_actions import IrActionsActClient


# @tagged("-at_install", "post_install")
class TestChangeCoordinator(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        # TODO: We must start using demo data for the test
        self.community = self.env["res.company"].browse(3)
        self.origin_coordinator = self.community.parent_id
        self.destination_coordinator = self.env["res.company"].browse(21)

    # Test main method inside wizard
    def test_change_coordinator(self):
        ###########################################################################################
        # WORKFLOW: Origin coordinator users have access to community
        ############################################################################################
        origin_coord_res_users = (
            self.env["res.users.role.line"]
            .search(
                [
                    (
                        "role_id",
                        "=",
                        self.env.ref("energy_communities.role_coord_admin").id,
                    ),
                    ("company_id", "=", self.origin_coordinator.id),
                ]
            )
            .mapped("user_id")
        )
        for origin_coord_user in origin_coord_res_users:
            # CHECK: community is defined on origin coord user company_ids
            self.assertEqual(
                bool(
                    origin_coord_user.company_ids.filtered(
                        lambda company: company.id == self.community.id
                    )
                ),
                True,
            )
            # CHECK: community is defined on origin coord user related partner company_ids
            self.assertEqual(
                bool(
                    origin_coord_user.partner_id.company_ids.filtered(
                        lambda company: company.id == self.community.id
                    )
                ),
                True,
            )
            # CHECK: origin coord user is a community manager of the community
            self.assertEqual(
                bool(
                    origin_coord_user.role_line_ids.filtered(
                        lambda role_line: (
                            role_line.role_id.id
                            == self.env.ref("energy_communities.role_ce_manager").id
                            and role_line.company_id.id == self.community.id
                        )
                    )
                ),
                True,
            )
        ###################################################
        # EXECUTE ACTION
        ###################################################
        self.community.change_coordinator(self.destination_coordinator, "testing")
        # CHECK: The community parent has been defined as destination_coordinator
        self.assertEqual(self.community.parent_id, self.destination_coordinator)
        ####################################################################################
        # WORKFLOW: Destination Coord admins have access to community
        ####################################################################################
        dest_coord_res_users = (
            self.env["res.users.role.line"]
            .search(
                [
                    (
                        "role_id",
                        "=",
                        self.env.ref("energy_communities.role_coord_admin").id,
                    ),
                    ("company_id", "=", self.destination_coordinator.id),
                ]
            )
            .mapped("user_id")
        )
        for dest_coord_user in dest_coord_res_users:
            # CHECK: community is defined on destination coord user company_ids
            self.assertEqual(
                bool(
                    dest_coord_user.company_ids.filtered(
                        lambda company: company.id == self.community.id
                    )
                ),
                True,
            )
            # CHECK: community is defined on destination coord user related partner company_ids
            self.assertEqual(
                bool(
                    dest_coord_user.partner_id.company_ids.filtered(
                        lambda company: company.id == self.community.id
                    )
                ),
                True,
            )
            # CHECK: destination coord user is a community manager of the community
            self.assertEqual(
                bool(
                    dest_coord_user.role_line_ids.filtered(
                        lambda role_line: (
                            role_line.role_id.id
                            == self.env.ref("energy_communities.role_ce_manager").id
                            and role_line.company_id.id == self.community.id
                        )
                    )
                ),
                True,
            )
        # CHECK: partner representing community has gained visibility on destination coordinator
        self.assertEqual(
            bool(
                self.community.partner_id.company_ids.filtered(
                    lambda company: company.id == self.destination_coordinator.id
                )
            ),
            True,
        )

        ###########################################################################################
        # WORKFLOW: Origin coordinator users lost CRUD access to community but preserves R (visibility)
        ############################################################################################
        origin_coord_res_users = (
            self.env["res.users.role.line"]
            .search(
                [
                    (
                        "role_id",
                        "=",
                        self.env.ref("energy_communities.role_coord_admin").id,
                    ),
                    ("company_id", "=", self.origin_coordinator.id),
                ]
            )
            .mapped("user_id")
        )
        for origin_coord_user in origin_coord_res_users:
            # CHECK: community is NOT DEFINED on origin coord user company_ids
            self.assertEqual(
                bool(
                    origin_coord_user.company_ids.filtered(
                        lambda company: company.id == self.community.id
                    )
                ),
                False,
            )
            # CHECK: community is NOT DEFINED on origin coord user related partner company_ids
            self.assertEqual(
                bool(
                    origin_coord_user.partner_id.company_ids.filtered(
                        lambda company: company.id == self.community.id
                    )
                ),
                False,
            )
            # CHECK: origin coord user is NO LONGER a community manager of the community
            self.assertEqual(
                bool(
                    origin_coord_user.role_line_ids.filtered(
                        lambda role_line: (
                            role_line.role_id.id
                            == self.env.ref("energy_communities.role_ce_manager").id
                            and role_line.company_id.id == self.community.id
                        )
                    )
                ),
                False,
            )
            # Origin Coord Admin still preserve visibility on community
            # CHECK Origin Coord admin community still preserve origin_coordinator in company_ids
            self.assertEqual(
                bool(
                    origin_coord_user.company_ids.filtered(
                        lambda company: company.id == self.origin_coordinator.id
                    )
                ),
                True,
            )
        # CHECK Partner representing community still preserve visibility on origin coordinator
        self.assertEqual(
            bool(
                self.community.partner_id.company_ids.filtered(
                    lambda company: company.id == self.origin_coordinator.id
                )
            ),
            True,
        )

    # Test wizard execution
    def test_change_coordinator_wizard(self):
        change_coordinator_wizard = self.env["change.coordinator.wizard"].create(
            {
                "incoming_coordinator": self.destination_coordinator.id,
                "change_reason": "testing",
            }
        )
        action_return = change_coordinator_wizard.with_context(
            {"active_ids": [self.community.id]}
        ).execute_change()
        self.assertEqual(action_return["params"]["type"], "success")
