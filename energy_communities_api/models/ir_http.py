from werkzeug.exceptions import HTTPException, Unauthorized

from odoo import models

from odoo.addons.base_rest.http import wrapJsonException


class IrHttpJwt(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _authenticate(cls, endpoint):
        try:
            super()._authenticate(endpoint)
        except (HTTPException, Unauthorized) as e:
            raise wrapJsonException(e, str(e))
