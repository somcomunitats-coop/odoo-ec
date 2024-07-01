import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

__all__ = ["post_init_hook"]


def post_init_hook(cr, rule_ref):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        instance_company = env.ref("base.main_company")
        instance_company.write({"hierarchy_level": "instance", "parent_id": False})
        coordinator_companies = instance_company.child_ids
        coordinator_companies.write({"hierarchy_level": "coordinator"})

        cr.execute(
            "UPDATE res_users_role SET priority=1 WHERE code = 'role_platform_admin'")
        cr.execute(
            "UPDATE res_users_role SET priority=2 WHERE code = 'role_coord_admin'")
        cr.execute(
            "UPDATE res_users_role SET priority=3 WHERE code = 'role_ce_admin'")

        # cr.execute(
        #     "UPDATE res_users_role SET priority=4 WHERE code = 'role_ce_manager'")
        # cr.execute(
        #     "UPDATE res_users_role SET priority=5 WHERE code = 'role_ce_member'")
        # cr.execute(
        #     "UPDATE res_users_role SET priority=6 WHERE code = 'role_coord_worker'")
        # cr.execute(
        #     "UPDATE res_users_role SET priority=7 WHERE code = 'role_internal_user'")

        roles = {}
        cr.execute("SELECT id,code from res_users_role")
        rols = cr.fetchall()
        for r in rols:
            roles[r[1]] = r[0]

        cr.execute(
            f"""INSERT INTO res_users_role_rel(rol_id,available_role_id) 
            VALUES ({roles['role_ce_member']},{roles['role_ce_member']})""")
        cr.execute(
            f"""INSERT INTO res_users_role_rel(rol_id,available_role_id) 
                    VALUES ({roles['role_ce_member']},{roles['role_ce_admin']})""")
        cr.execute(
            f"""INSERT INTO res_users_role_rel(rol_id,available_role_id) 
                    VALUES ({roles['role_ce_member']},{roles['role_ce_manager']})""")

        cr.execute(
            f"""INSERT INTO res_users_role_rel(rol_id,available_role_id) 
                    VALUES ({roles['role_ce_admin']},{roles['role_ce_member']})""")
        cr.execute(
            f"""INSERT INTO res_users_role_rel(rol_id,available_role_id) 
                    VALUES ({roles['role_ce_admin']},{roles['role_ce_admin']})""")
        cr.execute(
            f"""INSERT INTO res_users_role_rel(rol_id,available_role_id) 
                    VALUES ({roles['role_ce_admin']},{roles['role_ce_manager']})""")

        cr.commit()
