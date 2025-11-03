from odoo import _, api, fields, models

from odoo.addons.energy_communities.config import (
    CHART_OF_ACCOUNTS_GENERAL_REF,
    CHART_OF_ACCOUNTS_NON_PROFIT_REF,
)
from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_NON_PROFIT,
)


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = "account.multicompany.easy.creation.wiz"

    create_user = fields.Boolean(string="Create user for cooperator", default=False)
    capital_share = fields.Monetary(string="Initial capital share", default=100)

    @api.onchange("legal_form")
    def _onchange_legal_form_trigger(self):
        for record in self:
            if record.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
                if self.is_canary():
                    chart_of_account_ref = CHART_OF_ACCOUNTS_NON_PROFIT_CANARY_REF
                else:
                    chart_of_account_ref = CHART_OF_ACCOUNTS_NON_PROFIT_REF
            else:
                if self.is_canary():
                    chart_of_account_ref = CHART_OF_ACCOUNTS_GENERAL_CANARY_REF
                else:
                    chart_of_account_ref = CHART_OF_ACCOUNTS_GENERAL_REF
            record.chart_template_id = self.env.ref(chart_of_account_ref).id

    def thread_action_accept(self):
        super().thread_action_accept()
        self.new_company_id.write({"create_user": self.create_user})
        # rename SUBJ journal
        self.new_company_id.subscription_journal_id.sudo().write(
            {"code": "CS", "name": "Capital Social"}
        )
