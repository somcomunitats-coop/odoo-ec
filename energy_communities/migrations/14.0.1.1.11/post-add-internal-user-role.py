from odoo import SUPERUSER_ID, api

import logging

logger = logging.getLogger(__name__)





def migrate(cr, version):
    logger.info("Running post migration {}".format(version))
    env = api.Environment(cr, SUPERUSER_ID, {})
    internal_user_role = env['res.users.role'].search([
        ('code', '=', 'role_internal_user')
    ])
    role_lines = env['res.users.role.line'].search([
        ("role_id.code", "in", ['role_ce_admin', 'role_coordination', 'role_platform_admin'])
    ])
    logger.info("Founded this role lines: {}".format(role_lines))
    for line in role_lines:
        logger.info("Processing line {line_id} from user {user}".format(
            line_id=line.id, user=line.user_id.login
        ))
        is_internal_user = self.env['res.users.role.line'].search([
            ("user_id.id", "=", line.user_id.id),
            ("role_id.id", "=", internal_user_role.id),
        ])
        if not is_internal_user:
            self.env['res.users.role.line'].sudo().create({
                "user_id": line.user_id.id,
                "active": line.active,
                "role_id": internal_user_role.id,
            })
        elif is_internal_user and is_internal_user.active == False and line.active == True:
            is_internal_user.write({
                "active": line.active
            })
