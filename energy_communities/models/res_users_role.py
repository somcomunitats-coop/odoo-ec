from odoo import fields, models, api

class ResUsersRoleLine(models.Model):
    _inherit = 'res.users.role.line'

    company_id = fields.Many2one(
        string='Companyia',
        comodel_name='res.company',
        default=lambda self: self.env["res.company"]._company_default_get()
    )


            
        

