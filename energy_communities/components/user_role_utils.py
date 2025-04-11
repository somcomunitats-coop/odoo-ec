from odoo.addons.component.core import Component


class UserRoleUtils(Component):
    _name = "user.role.utils"
    _usage = "user.role.utils"
    _apply_on = "res.users"
    _collection = "utils.backend"

    # def add_energy_community_role(self, company_id, role_name):
    #     if role_name == "role_ce_member" or role_name == "role_ce_admin":
    #         self.make_ce_user(company_id, role_name)
    #     elif role_name == "role_coord_admin":
    #         self.make_coord_user(company_id, role_name)
    #     else:
    #         raise exceptions.UserError(_("Role not found"))

    def apply_role_in_company(self, role_code, company_id):
        update_dict = {}
        # existing_company = self.work.record.company_ids.filtered(
        #     lambda company: company.id == company_id.id
        # )
        # if not existing_company:
        update_dict["company_ids"] = [(4, company_id.id)]
        existing_role = self.get_related_role(role_code, company_id)
        if not existing_role:
            update_dict["role_line_ids"] = [
                (
                    0,
                    0,
                    {
                        "active": True,
                        "role_id": self.env.ref(
                            "energy_communities.{}".format(role_code)
                        ).id,
                        "user_id": self.work.record.id,
                        "company_id": company_id.id,
                    },
                )
            ]
        self.work.record.write(update_dict)

    def apply_coordinator_role_in_company(self, company_id):
        self.apply_role_in_company("role_coord_admin", company_id)
        child_companies = company_id.get_child_companies()
        for child_company in child_companies:
            self.apply_role_in_company("role_ce_manager", child_company)

    def get_related_role(self, role_code, company_id=False):
        query = [
            ("user_id", "=", self.work.record.id),
            ("code", "=", role_code),
            ("active", "=", True),
        ]
        if company_id:
            query.append(("company_id", "=", company_id.id))
        return self.env["res.users.role.line"].search(query)
