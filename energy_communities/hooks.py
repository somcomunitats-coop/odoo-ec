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
