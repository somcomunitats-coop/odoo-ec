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
