from odoo import api, models, fields, _

class CmPlace(models.Model):
    _inherit = 'crm.team'

    community_company_id = fields.Many2one(        
        string='Related Community',
        comodel_name='res.company',
        domain="[('coordinator','!=',True)]",
        help="Community related to this Map point"
    )
 