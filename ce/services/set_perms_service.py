# Copyright 2019 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=consider-merging-classes-inherited

import logging

from werkzeug.exceptions import BadRequest, NotFound

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.base_rest.http import wrapJsonException
from odoo.addons.component.core import Component
from . import schemas


_logger = logging.getLogger(__name__)


class SetPermsService(Component):
    _inherit = "emc.rest.service"
    _name = "set.perms.services"
    _usage = "set-perms-request"
    _description = """
        Reset Permission Request Services
    """

    def set_perms(self, **params):
        """
        User must be active in the company.
        "company_id"
        "user_id"
        "target_company_id"
        "target_user_id"
        "new_role_id"
        """

        _logger.info("Requested set-perms, user: {}, target_company: {}, target user: {}, perms: {}"
            .format(params["user_id"], params["target_company_id"], params["target_user_id"], params["new_role_id"]))

        domain = [('company_id', '=', params["company_id"]),
            ('oauth_uid', '=', params["user_id"])]
        user = self.env["res.users"].search(domain)

        target_domain = [('company_id', '=', params["target_company_id"]),
            ('oauth_uid', '=', params["target_user_id"])]
        target_user = self.env["res.users"].search(target_domain)

        if not user:
            raise wrapJsonException(BadRequest(
                _("User {} not found in company {}").format(params["user_id"], params["company_id"])))
        if not target_user:
            raise wrapJsonException(BadRequest(
                _("User {} not found in company {}").format(params["targe_user_id"], params["target_company_id"])))

        role_domain = [('name', '=', params["new_role_id"])] #TODO: està patillat
        new_role = self.env["res.users.role"].search(role_domain)

        if not new_role:
            raise wrapJsonException(BadRequest(
                _("Role {} not found in company {}").format(params["targe_user_id"], params["target_company_id"])))

        values = {}
        res = self.env["res.users"].write(target_user, values)
        return {"message": res}

    def _prepare_create(self, params):
        """Prepare a writable dictionary of values"""
        return {
            "company_id": params["company_id"],
            "user_id": params["user_id"],
            "target_company_id": params["target_company_id"],
            "target_user_id": params["target_user_id"],
            "new_role_id": params["new_role_id"],
        }


    def _validator_set_perms(self):
        return schemas.S_SET_PERMS_REQUEST_GET

    def _validator_return_set_perms(self):
        return schemas.S_SET_PERMS_REQUEST_RETURN


