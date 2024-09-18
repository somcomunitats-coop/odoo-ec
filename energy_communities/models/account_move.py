import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..utils import user_creator


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_date = fields.Date(compute="_compute_payment_date", store=False)

    def _compute_payment_date(self):
        for record in self:
            dates = []
            for payment_info in json.loads(record.invoice_payments_widget).get(
                "content", []
            ):
                dates.append(payment_info.get("date", ""))
            if dates:
                dates.sort()
                record.payment_date = dates[0]

    def create_user(self, partner):
        user_obj = self.env["res.users"]
        vat = partner.vat

        user = user_obj.search([("login", "=", vat)])
        if not user:
            user = user_obj.search([("login", "=", vat), ("active", "=", False)])
            if user:
                user.sudo().write({"active": True})

        role_id = self.env.ref("energy_communities.role_ce_member")
        action = "create_user"
        if partner.company_id.create_user_in_keycloak:
            action = "create_kc_user"
        with user_creator(self.env) as component:
            component.create_users_from_cooperator_partners(
                partners=partner, role_id=role_id, action=action, force_invite=False
            )
        return user
