from odoo import _, api, fields, models


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = [
        "account.multicompany.easy.creation.wiz",
        "contract.recurrency.basic.mixin",
    ]

    def thread_action_accept(self):
        super().thread_action_accept()
