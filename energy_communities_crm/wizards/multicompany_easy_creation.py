from odoo import _, api, fields, models


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = "account.multicompany.easy.creation.wiz"

    def action_accept(self):
        success_msg = super().action_accept()
        # create default sale team for new company
        self.env["crm.team"].get_create_default_sale_team(self.new_company_id)
        # create default stages for new company
        self.env["crm.stage"].get_create_default_stages(self.new_company_id)
        return success_msg
