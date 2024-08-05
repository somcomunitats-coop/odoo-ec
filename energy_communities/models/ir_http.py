from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        """
        Based on the selected companies (cids),
        calculate the roles to enable.
        A role should be enabled only for the active selected company.
        """
        result = super().session_info()
        if self.env.user.role_line_ids:
            cids = request.httprequest.cookies.get("cids")
            self.env.user.with_context(
                allowed_company_ids=[int(cids[0])]
            ).set_groups_from_roles()
        return result
