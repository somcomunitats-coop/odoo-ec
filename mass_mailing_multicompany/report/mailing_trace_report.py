from odoo import fields, models


class MailingTraceReport(models.Model):
    # _name = 'mailing.trace.report'
    _inherit = "mailing.trace.report"

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
