# Add faker into requirements.txt ?? 🤔
from faker import Faker
from odoo.tests import common
from odoo.exceptions import UserError


faker = Faker(locale='es_ES')

class TestResUsers(common.TransactionCase):

    def create_company(self, name, hierarchy_level, parent_id):
        return self.company_model.create({
            'name': name,
            'hierarchy_level': hierarchy_level,
            'parent_id': parent_id,
        })

    def create_user(self, firstname, lastname):
        return self.users_model.create({
            "login": faker.vat_id(),
            "firstname": firstname,
            "lastname": lastname,
            "email": faker.email(),
        })

    def setUp(self):
        super().setUp()

        self.users_model = self.env['res.users']
        self.company_model = self.env['res.company']
        self.role_line_model = self.env["res.users.role.line"]
        self.instance = self.company_model.search([
            ('hierarchy_level', '=', 'instance')
        ])[0]

        self.coordination = self.create_company(
            'Coordinator', 'coordinator', self.instance.id,
        )
        self.community = self.create_company(
            'Energy Community', 'community', self.coordination.id,
        )
        
        self.platform_admin = self.create_user("Platform", "Admin")
        self.community_admin = self.create_user("Community", "Admin")
        self.random_user = self.create_user("Brandom", "Random")

        self.community_admin.write({
            "company_ids": [(4, self.community.id)]
        })
        self.admin_role = self.env["res.users.role"].search([(
            "code", "=", 'role_ce_admin'
        )])
        self.role_line_model.create({
            "user_id": self.community_admin.id,
            "active": True,
            "role_id": self.admin_role.id,
            "company_id": self.community.id,
        })
        self.internal_role = self.env["res.users.role"].search([(
            "code", "=", "role_internal_user"
        )])
        self.role_line_model.create({
            "user_id": self.community_admin.id,
            "active": True,
            "role_id": self.internal_role.id,
        })

    def test__create_energy_community_base_user__base_case(self):
        # Patch is required 🌞
        pass

    def test__add_energy_community_role__make_ce_user(self):
        # Patch is required 🌞
        pass

    def test__add_energy_community_role__make_coord_user(self):
        # Patch is required 🌞
        pass

    def test__add_energy_community_role__role_not_found(self):
        with self.assertRaises(UserError):
            self.users_model.add_energy_community_role(
                role_name="onering_owner",
                company_id=self.coordination.id,
            )

    def test__make_ce_user__already_user(self):
        self.community_admin.make_ce_user(self.community.id, "role_ce_member")

        rl = self.role_line_model.search([
            ("user_id", "=", self.community_admin.id),
            ("company_id", "=", self.community.id),
        ])
        self.assertEqual(len(rl), 1)
        self.assertEqual(rl[0].role_id.code, "role_ce_member")
        self.assertIn(
            self.community,
            self.community_admin.company_ids
        )

    def test__make_ce_user__new_user(self):
        self.random_user.make_ce_user(self.community.id, "role_ce_member")

        rl = self.role_line_model.search([
            ("user_id", "=", self.random_user.id),
            ("role_id.code", "=", "role_ce_member"),
            ("company_id", "=", self.community.id),
        ])
        self.assertEqual(len(rl), 1)
        self.assertIn(
            self.community,
            self.random_user.company_ids
        )

    def test__make_internal_user__new_user(self):
        # When we call make_internal_user with a new user
        self.random_user.make_internal_user()

        # Then creates new role_line with "role_internal_user"
        role_lines = self.role_line_model.search([
            ("user_id", "=", self.random_user.id),
            ("role_id.code", "=", "role_internal_user"),
        ])
        self.assertEqual(len(role_lines), 1)
        role_line = role_lines[0]
        # and role_line has not company
        self.assertEqual(list(role_line.company_id), [])

    def test__make_internal_user__already_user(self):
        # When we call make_internal_user with existing user
        self.community_admin.make_internal_user()

        # Then anything is created
        rl = self.role_line_model.search([
            ("user_id", "=", self.community_admin.id),
            ("role_id.code", "=", "role_internal_user"),
        ])
        self.assertEqual(len(rl), 1)
