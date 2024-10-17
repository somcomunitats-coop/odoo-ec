from odoo import models


class UtilsBackend(models.Model):
    _name = "utils.backend"
    _inherit = "collection.base"
    _description = "Utils backend"
