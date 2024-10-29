from odoo import _, api, fields, models


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = "account.multicompany.easy.creation.wiz"

    def create_default_utm_stage(self):
        self.env["utm.stage"].sudo().create(
            {"name": _("New"), "company_id": self.new_company_id.id}
        )

    def thread_action_accept(self):
        super().thread_action_accept()
        self.create_default_utm_stage()
