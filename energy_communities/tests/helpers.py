from faker import Faker


faker = Faker(locale='es_ES')

class CompanySetupMixin(object):

    def create_company(self, name, hierarchy_level, parent_id):
        return self.env["res.company"].create({
            'name': name,
            'hierarchy_level': hierarchy_level,
            'parent_id': parent_id,
        })

class UserSetupMixin(object):

    def create_user(self, firstname, lastname, vat=False, email=False):
        login = vat if vat else faker.vat_id()
        return self.env["res.users"].create({
            "login": login.lower(),
            "firstname": firstname,
            "lastname": lastname,
            "email": email if email else faker.email(),
        })

    def make_community_admin(self, community_admin):
        community_admin.write({"company_ids": [(4, self.community.id)]})
        self.admin_role = self.env["res.users.role"].search([(
            "code", "=", 'role_ce_admin'
        )])
        self.env["res.users.role.line"].create({
            "user_id": community_admin.id,
            "active": True,
            "role_id": self.admin_role.id,
            "company_id": self.community.id,
        })
        self.internal_role = self.env["res.users.role"].search([(
            "code", "=", "role_internal_user"
        )])
        self.env["res.users.role.line"].create({
            "user_id": community_admin.id,
            "active": True,
            "role_id": self.internal_role.id,
        })

    def add_role(self, user, role_code, company=None):
        role = self.env["res.users.role"].search([(
            "code", "=", role_code
        )])
        vals = {
            "user_id": user.id,
            "active": True,
            "role_id": role.id,
        }
        if company:
            vals["company_id"] = company.id

        self.env["res.users.role.line"].create(vals)

    def make_coord_user(
        self, coord_company, coord_admin, role="role_coord_admin", community=None
    ):
        coord_admin.write({"company_ids": [(4, coord_company.id)]})
        self.add_role(coord_admin, role, coord_company)
        self.add_role(coord_admin, "role_internal_user")

        if community:
            self.add_role(coord_admin, "role_ce_manager", community)
