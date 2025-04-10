# Copyright 2020 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class TicketBaiGeneralInfo(models.TransientModel):
    _inherit = "tbai.info"

    tbai_enabled = fields.Boolean(
        default=lambda self: self.env.user.partner_id.company_id.tbai_enabled
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.user.partner_id.company_id,
    )
