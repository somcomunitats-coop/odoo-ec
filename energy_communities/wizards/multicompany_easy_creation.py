from odoo import fields, models, api


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _inherit = "account.multicompany.easy.creation.wiz"

    crm_lead_id = fields.Many2one('crm.lead', string="CRM Lead")