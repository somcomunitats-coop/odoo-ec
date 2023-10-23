from faker import Faker

faker = Faker(locale="es_ES")


class CompanySetupMixin:
    def create_company(self, name, hierarchy_level, parent_id):
        return self.company_model.create(
            {
                "name": name,
                "hierarchy_level": hierarchy_level,
                "parent_id": parent_id,
            }
        )


class UserSetupMixin:
    def create_user(self, firstname, lastname, vat=False, email=False):
        login = vat if vat else faker.vat_id()
        return self.users_model.create(
            {
                "login": login.upper(),
                "firstname": firstname,
                "lastname": lastname,
                "email": email if email else faker.email(),
            }
        )

    def make_community_admin(self, community_admin):
        community_admin.write({"company_ids": [(4, self.community.id)]})
        self.admin_role = self.env["res.users.role"].search(
            [("code", "=", "role_ce_admin")]
        )
        self.role_line_model.create(
            {
                "user_id": community_admin.id,
                "active": True,
                "role_id": self.admin_role.id,
                "company_id": self.community.id,
            }
        )
        self.internal_role = self.env["res.users.role"].search(
            [("code", "=", "role_internal_user")]
        )
        self.role_line_model.create(
            {
                "user_id": community_admin.id,
                "active": True,
                "role_id": self.internal_role.id,
            }
        )

    def make_coord_admin(self, coord_admin):
        coord_admin.write({"company_ids": [(4, self.coordination.id)]})
        coord_admin.write({"company_ids": [(4, self.community.id)]})
        coord_admin_role = self.env["res.users.role"].search(
            [("code", "=", "role_coord_admin")]
        )
        self.role_line_model.create(
            {
                "user_id": coord_admin.id,
                "active": True,
                "role_id": coord_admin_role.id,
                "company_id": self.community.id,
            }
        )
        self.ce_manager_role = self.env["res.users.role"].search(
            [("code", "=", "role_ce_manager")]
        )
        self.role_line_model.create(
            {
                "user_id": coord_admin.id,
                "active": True,
                "role_id": self.ce_manager_role.id,
                "company_id": self.community.id,
            }
        )
        self.internal_role = self.env["res.users.role"].search(
            [("code", "=", "role_internal_user")]
        )
        self.role_line_model.create(
            {
                "user_id": coord_admin.id,
                "active": True,
                "role_id": self.internal_role.id,
            }
        )
