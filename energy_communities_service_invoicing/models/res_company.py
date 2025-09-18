from odoo import models

from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_NON_PROFIT,
)

from ..config import (
    COOP_ACCOUNT_REF,
    COOP_ACCOUNT_REF_NONPROFIT,
    RECURRING_FEE_ACCOUNT_REF,
    RECURRING_FEE_ACCOUNT_REF_NONPROFIT,
)


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    def get_company_coop_account(self):
        # select cooperator account to be used
        if self.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            return self.env.ref(COOP_ACCOUNT_REF_NONPROFIT.format(self.id))

        return self.env.ref(COOP_ACCOUNT_REF.format(self.id))

    def get_company_share_recurring_fee_service_account(self):
        if self.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            return self.env.ref(RECURRING_FEE_ACCOUNT_REF_NONPROFIT.format(self.id))

        return self.env.ref(RECURRING_FEE_ACCOUNT_REF.format(self.id))
