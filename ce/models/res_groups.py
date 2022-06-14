from odoo import api, models, fields, _

class ResGroups(models.Model):
    _inherit = 'res.groups'

    @api.multi
    def _get_kc_user_group(self):
        for rg in self:
            pass