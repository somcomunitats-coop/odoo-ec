import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})

    internal_user_role = env.ref("energy_communities.role_internal_user")

    odoo_base_user_ids = [
        u.id
        for u in (
            env.ref("base.user_root"),
            env.ref("base.user_admin"),
            env.ref("base.default_user"),
            env.ref("base.public_user"),
            env.ref("base.template_portal_user_id"),
        )
    ]

    instance_company_id = env["res.company"].search(
        [("hierarchy_level", "=", "instance")]
    )
    logger.info(
        "Running post migration {}. Instance company: {}".format(
            version, instance_company_id.name
        )
    )
    coordinator_company_ids = env["res.company"].search(
        [("hierarchy_level", "=", "coordinator")]
    )
    logger.info(
        "Running post migration {}. Coordinator companies: {}".format(
            version, coordinator_company_ids.mapped("name")
        )
    )

    # get all target users to manage
    target_users = env["res.users"].search([("id", "not in", odoo_base_user_ids)])
    logger.info(
        "Running post migration {}. All Target users ({}): {}".format(
            version, len(target_users), str(target_users.mapped("name"))
        )
    )

    # get users that must be setted as platform_admins
    target_users_platform_admins = target_users.filtered(
        lambda u: instance_company_id in u.company_ids
    )
    logger.info(
        "Running post migration {}. Platform admin users ({}): {}".format(
            version,
            len(target_users_platform_admins),
            str(target_users_platform_admins.mapped("name")),
        )
    )

    target_users = target_users - target_users_platform_admins

    # get users that must be setted as coordinator_admins
    target_users_coordinator_admins = env["res.users"]
    for u in target_users:
        if u.company_ids & coordinator_company_ids:
            target_users_coordinator_admins |= u
    logger.info(
        "Running post migration {}. Coordinator admin users ({}): {}".format(
            version,
            len(target_users_coordinator_admins),
            str(target_users_coordinator_admins.mapped("name")),
        )
    )

    # get users that must be setted as CE users (admin or member) per its company_ids
    target_users = target_users - target_users_coordinator_admins
    logger.info(
        "Running post migration {}. CE admn & member users ({}): {}".format(
            version, len(target_users), str(target_users.mapped("name"))
        )
    )

    # loop1 --> update the plattform_admin_users
    for u in target_users_platform_admins:
        logger.info(
            "Running post migration {}. Platform admin users: {}".format(
                version, u.name
            )
        )

        # delete all existing role lines
        u.write({"role_line_ids": [(5, 0, 0)]})
        # add the internal role
        u.write(
            {
                "role_line_ids": [
                    (
                        0,
                        0,
                        {
                            "user_id": u.id,
                            "active": True,
                            "role_id": internal_user_role.id,
                        },
                    )
                ]
            }
        )
        # add the platform admin role
        u.write(
            {
                "role_line_ids": [
                    (
                        0,
                        0,
                        {
                            "user_id": u.id,
                            "active": True,
                            "role_id": env.ref(
                                "energy_communities.role_platform_admin"
                            ).id,
                        },
                    )
                ]
            }
        )

    # loop2 --> update the Coordinators users
    for u in target_users_coordinator_admins:
        logger.info(
            "Running post migration {}. Coordinator admin users: {}".format(
                version, u.name
            )
        )

        original_company_ids = env["res.company"].browse(u.company_ids.mapped("id"))
        logger.info(
            "Original user companies {}".format(original_company_ids.mapped("name"))
        )

        # get the companies that are sons of the Coordinator ones
        coord_company_ids = u.company_ids & coordinator_company_ids
        logger.info("Coordinator companies {}".format(coord_company_ids.mapped("name")))

        coord_hierarchy_company_ids = env["res.company"]
        for coord_c in coord_company_ids:
            coord_hierarchy_company_ids |= env["res.company"].search(
                [("hierarchy_level", "=", "community"), ("parent_id", "=", coord_c.id)]
            )
        logger.info(
            "Sons of coord companies {}".format(
                coord_hierarchy_company_ids.mapped("name")
            )
        )

        # delete all existing role lines
        u.write({"role_line_ids": [(5, 0, 0)]})

        # add the internal role
        u.write(
            {
                "role_line_ids": [
                    (
                        0,
                        0,
                        {
                            "user_id": u.id,
                            "active": True,
                            "role_id": internal_user_role.id,
                        },
                    )
                ]
            }
        )

        # update the user company_ids
        for c in coord_hierarchy_company_ids:
            if c not in original_company_ids:
                logger.info("Company added to user {}".format(c.name))
                u.write({"company_ids": [(4, c.id)]})

        # add the coord_admin role
        for coord_c in coord_company_ids:
            u.write(
                {
                    "role_line_ids": [
                        (
                            0,
                            0,
                            {
                                "company_id": coord_c.id,
                                "user_id": u.id,
                                "active": True,
                                "role_id": env.ref(
                                    "energy_communities.role_coord_admin"
                                ).id,
                            },
                        )
                    ]
                }
            )

        # add the ce_manager role
        for coord_son in coord_hierarchy_company_ids:
            u.write(
                {
                    "role_line_ids": [
                        (
                            0,
                            0,
                            {
                                "company_id": coord_son.id,
                                "user_id": u.id,
                                "active": True,
                                "role_id": env.ref(
                                    "energy_communities.role_ce_manager"
                                ).id,
                            },
                        )
                    ]
                }
            )

        # add role_line (member_ce) for the companies that are not under the coordinator ones
        # TODO: it can be that a user originally has a role different than ce_member for those companies
        # that are not under the Coordinator's hierarchy, but we here are simplifiying and assigning ce_member
        full_hierarchy_company_ids = coord_hierarchy_company_ids | coord_company_ids
        for not_coord_hie_c in original_company_ids - full_hierarchy_company_ids:
            u.write(
                {
                    "role_line_ids": [
                        (
                            0,
                            0,
                            {
                                "company_id": not_coord_hie_c.id,
                                "user_id": u.id,
                                "active": True,
                                "role_id": env.ref(
                                    "energy_communities.role_ce_member"
                                ).id,
                            },
                        )
                    ]
                }
            )

    # loop3 --> update the CE users (u)
    for u in target_users:
        role_to_use = env.ref("energy_communities.role_ce_member")
        already_has_internal = False
        # get the roles in role_lines that don't have any company_id mantained
        roles_no_company = list(
            {rl.role_id for rl in u.role_line_ids if (not rl.company_id and rl.active)}
        )
        for r in roles_no_company:
            if r == internal_user_role:
                already_has_internal = True
            if r in (
                env.ref("energy_communities.role_ce_admin"),
                env.ref("energy_communities.role_ce_manager"),
                env.ref("energy_communities.role_coord_admin"),
                env.ref(
                    "energy_communities.role_platform_admin",
                ),
            ):
                role_to_use = env.ref("energy_communities.role_ce_admin")

        # review & clean all existing role_line_ids &
        # get the role_lines that already have
        companies_with_role_line = []
        for rl_id in [l.id for l in u.role_line_ids]:
            rl = env["res.users.role.line"].browse([rl_id])
            if not rl.company_id:
                if rl.role_id != internal_user_role:
                    u.write({"role_line_ids": [(3, rl_id)]})
            else:  # role_lines with company assigned
                if not rl.active:
                    u.write({"role_line_ids": [(3, rl_id)]})
                elif rl.company_id not in u.company_ids:
                    u.write({"role_line_ids": [(3, rl_id)]})
                else:
                    companies_with_role_line.append(rl.company_id)

        # add internal role if needed
        if not already_has_internal:
            u.write(
                {
                    "role_line_ids": [
                        (
                            0,
                            0,
                            {
                                "user_id": u.id,
                                "active": True,
                                "role_id": internal_user_role.id,
                            },
                        )
                    ]
                }
            )

        # add remaining per company role_lines
        for c in u.company_ids:
            if c not in companies_with_role_line:
                u.write(
                    {
                        "role_line_ids": [
                            (
                                0,
                                0,
                                {
                                    "company_id": c.id,
                                    "user_id": u.id,
                                    "active": True,
                                    "role_id": role_to_use.id,
                                },
                            )
                        ]
                    }
                )
