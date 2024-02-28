from odoo import api, fields, models


class MassMailingList(models.Model):
    _name = "mailing.list"
    _inherit = ["mailing.list", "user.currentcompany.mixin"]

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    sync_domain = fields.Char(
        string="Synchronization critera",
        default="[('is_blacklisted', '=', False),('email', '!=', False),('company_ids', '!=', False)]",
        required=True,
        help="Filter partners to sync in this list",
    )
