from odoo import _, api, fields, models

from odoo.addons.energy_communities.utils import (
    get_successful_popup_message,
    product_utils,
)


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = [
        "account.multicompany.easy.creation.wiz",
        "contract.recurrency.basic.mixin",
    ]

    def thread_action_accept(self):
        super().thread_action_accept()
        self._create_default_pricelist()

    def _create_default_pricelist(self):
        with product_utils(self.env) as component:
            return component.create_company_pricelist(self.new_company_id)
