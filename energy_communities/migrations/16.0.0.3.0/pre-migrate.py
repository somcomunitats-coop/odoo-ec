import logging

from odoo import SUPERUSER_ID, _, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info(f"Starting migration from version {version}.")
    _logger.info("Deleting role_coord_worker")
    res_user_role_coord_worker = env["res.users.role"].search(
        [("name", "=", _("Coordinator Worker"))]
    )
    if res_user_role_coord_worker:
        res_user_role_coord_worker.unlink()
        _logger.info("Deleted role_coord_worker")
    res_group_coord_worker = env["res.groups"].search(
        [("name", "=", _("Coordinator Worker"))]
    )
    if res_group_coord_worker:
        for model_acces in res_group_coord_worker.model_access:
            model_acces.unlink()
        _logger.info("Deleted model_access")
        for rule_group in res_group_coord_worker.rule_groups:
            rule_group.unlink()
        _logger.info("Deleted rule_groups")
        res_group_coord_worker.unlink()
        _logger.info("Deleted res.groups.coord_worker")
    _logger.info("Migration completed.")
