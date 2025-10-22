from odoo import api, fields, models


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = "account.multicompany.easy.creation.wiz"

    def thread_action_accept(self):
        super().thread_action_accept()
        # create default sale team for new company
        self.env["crm.team"].get_create_default_sale_team(self.new_company_id)
        # create default stages for new company
        self.env["crm.stage"].get_create_default_stages(self.new_company_id)

    @api.model
    def _get_company_creation_related_users_list(self, company_id):
        users = [user.id for user in company_id.get_users()] + [
            self.env.ref("base.public_user").id
        ]
        if self.env.ref("base.user_admin").id not in users:
            users = users + [self.env.ref("base.user_admin").id]
        return users
