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
            cookie_cids = request.httprequest.cookies.get("cids")
            try:
                cid = (
                    cookie_cids
                    and int(cookie_cids.split(",")[0])
                    or self.env.company.id
                )
            except Exception:
                cid = self.env.company.id
            self.env.user.with_context(
                allowed_company_ids=[cid]
            ).set_groups_from_roles()
        return result
