from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move.line"

    selfconsumption_id = fields.One2many(
        'energy_selfconsumption.selfconsumption',
        related="contract_line_id.contract_id.project_id.selfconsumption_id"
    )