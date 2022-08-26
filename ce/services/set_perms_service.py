# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=consider-merging-classes-inherited

import logging
from werkzeug.exceptions import BadRequest, NotFound
from odoo import _
from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from . import schemas


_logger = logging.getLogger(__name__)

class PermsService(Component):
    _inherit = "base.rest.private_abstract_service"
    _name = "ce.perms.services"
    _usage = "perms"
    _description = """
        Permission Request Services
    """

    def set_perms(self, **params):
        """
        User must be active in the company.
        "company_id"
        "user_id"
        "target_company_id"
        "target_user_id"
        "new_role"
        """

        _logger.info("Requested set_perms, user: {}, target_company: {}, target user: {}, perms: {}"
            .format(params["user_id"], params["target_company_id"], params["target_user_id"], params["new_role"]))

        domain = [('company_id', '=', int(params["company_id"])),
            ('oauth_uid', '=', params["user_id"])]
        user = self.env["res.users"].search(domain)

        if not user:
            raise wrapJsonException(
                BadRequest(
                    _("User {} not found in company {}").format(
                        params["user_id"],
                        params["company_id"])
                ),
                include_description=True,
            )

        target_domain = [('company_id', '=', int(params["target_company_id"])),
            ('oauth_uid', '=', params["target_user_id"])]
        target_user = self.env["res.users"].sudo(user.id).search(target_domain)

        if not target_user:
            raise wrapJsonException(
                BadRequest(
                    _("User {} not found in company {}").format(
                        params["targe_user_id"],
                        params["target_company_id"])
                ),
                include_description=True,
            )
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ce_member_key = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_member')
        ce_member_value = ICPSudo.get_param('ce.odoo_group_ce_member')
        ce_admin_key = ICPSudo.get_param('ce.ck_user_group_mapped_to_odoo_group_ce_admin')
        ce_admin_value = ICPSudo.get_param('ce.odoo_group_ce_admin')
        groups_map = { ce_member_key: ce_member_value, ce_admin_key: ce_admin_value }
        new_role = params['new_role']
        if not new_role in groups_map.keys():
            raise wrapJsonException(
                BadRequest(
                    _("Role {} not found!").format(
                        params["new_role"])
                ),
                include_description=True,
            )

        try:
            RoleSudo = self.env['res.users.role'].sudo(user.id)
            if target_user.role_ids:
                target_user.role_line_ids.unlink()
            new_role_record = RoleSudo.browse(int(groups_map[new_role]))
            ret_value = new_role_record.write({'users': [(4, target_user.id)]})
            target_user.role_line_ids.create(
                {'user_id': target_user.id, 'role_id': int(groups_map[new_role])})
            return {"message": ret_value}

        except Exception as e:
            raise wrapJsonException(
                BadRequest(str(e)),
                include_description=True,
            )

    def _prepare_create(self, params):
        """Prepare a writable dictionary of values"""
        return {
            "company_id": params["company_id"],
            "user_id": params["user_id"],
            "target_company_id": params["target_company_id"],
            "target_user_id": params["target_user_id"],
            "new_role": params["new_role"],
        }

    def _validator_set_perms(self):
        return schemas.S_SET_PERMS_REQUEST_GET

    def _validator_return_set_perms(self):
        return schemas.S_SET_PERMS_REQUEST_RETURN
