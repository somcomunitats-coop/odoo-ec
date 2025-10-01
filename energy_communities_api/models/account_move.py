import logging

from odoo import api, fields, models

logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    payment_state_for_api = fields.Char(compute="_compute_payment_state_for_api")

    @api.depends("state", "payment_state", "display_name")
    def _compute_payment_state_for_api(self):
        for record in self:
            record.payment_state_for_api = (
                record.state == "draft" and record.state or record.payment_state
            )
            if not record.payment_state_for_api:
                logger.warning(
                    "This is strange, invoice %s is not draft and payment_state is False",
                    record.display_name,
                )
                record.payment_state_for_api = "not_paid"
