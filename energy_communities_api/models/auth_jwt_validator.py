from werkzeug.exceptions import Unauthorized

from odoo import _, api, fields, models

JWT_DYNAMIC = "jwt-dynamic"
RELATED_USER = "related-user"

USER_ID_STRATEGIES = [(JWT_DYNAMIC, _("JWT Dynamic"))]

PARTNER_ID_STRATEGIES = [(RELATED_USER, _("Related User"))]


class AuthJwtValidator(models.Model):
    _name = "auth.jwt.validator"
    _inherit = "auth.jwt.validator"
    _description = _("JWT Validator Energy Communties costumizations")

    user_id_strategy = fields.Selection(
        selection_add=USER_ID_STRATEGIES, ondelete={JWT_DYNAMIC: "set default"}
    )
    partner_id_strategy = fields.Selection(
        selection_add=PARTNER_ID_STRATEGIES,
    )

    @api.onchange("user_id_strategy")
    @api.constrains("user_id_strategy")
    def _on_change_user_id_strategy(self):
        for record in self:
            if record.user_id_strategy == JWT_DYNAMIC:
                record.partner_id_strategy = RELATED_USER
            else:
                record.partner_id_strategy = "email"

    def _get_jwt_user(self, payload):
        username = payload.get("preferred_username", "").upper()
        user = self.env["res.users"].sudo().search([("login", "=", username)])
        if not user:
            raise Unauthorized(f"User with vat {username} not found")
        return user

    def _get_uid(self, payload):
        uid = super()._get_uid(payload)
        if self.user_id_strategy == JWT_DYNAMIC:
            user = self._get_jwt_user(payload)
            return user.id
        return uid

    def _get_partner_id(self, payload):
        pid = super()._get_partner_id(payload)
        if self.partner_id_strategy == RELATED_USER:
            return self._get_jwt_user(payload).partner_id.id
        return pid
