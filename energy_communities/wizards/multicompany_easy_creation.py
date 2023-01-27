from odoo import fields, models, api


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _inherit = "account.multicompany.easy.creation.wiz"

    crm_lead_id = fields.Many2one('crm.lead', string="CRM Lead")
    property_cooperator_account = fields.Many2one(
        comodel_name="account.account",
        string="Cooperator Account",
        domain=[
            ("internal_type", "=", "receivable"),
            ("deprecated", "=", False),
        ],
        help="This account will be"
             " the default one as the"
             " receivable account for the"
             " cooperators",
    )
