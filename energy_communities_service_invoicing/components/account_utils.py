# from typing import List
# from odoo import _
# from odoo.exceptions import ValidationError

from odoo.addons.account.models.account_journal import AccountJournal
from odoo.addons.base.models.res_company import Company
from odoo.addons.component.core import Component
from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_NON_PROFIT,
)

from ..config import (
    COOP_ACCOUNT_REF_GENERAL,
    COOP_ACCOUNT_REF_IN_COMPANY,
    COOP_ACCOUNT_REF_NONPROFIT,
    COOP_SHARE_PRODUCT_CATEG_REF,
)


class AccountUtils(Component):
    _inherit = "account.utils"

    def setup_company_cooperator_accounting_configuration(
        self, company: Company
    ) -> None:
        # select cooperator account to be used
        if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            cooperator_account = self.env.ref(
                COOP_ACCOUNT_REF_NONPROFIT.format(company.id)
            )
        else:
            cooperator_account = self.env.ref(
                COOP_ACCOUNT_REF_GENERAL.format(company.id)
            )
        # define company cooperator account
        company.write(
            {
                "property_cooperator_account": self.env.ref(
                    COOP_ACCOUNT_REF_IN_COMPANY.format(company.id)
                )
            }
        )
        # move to cooperator journal
        company.subscription_journal_id.write(
            {"default_account_id": cooperator_account.id}
        )
        # move to product category
        self.env.ref(COOP_SHARE_PRODUCT_CATEG_REF).with_company(company).write(
            {
                "service_invoicing_sale_journal_id": company.subscription_journal_id.id,
                "service_invoicing_purchase_journal_id": company.subscription_journal_id.id,
                "property_account_income_categ_id": cooperator_account.id,
                "property_account_expense_categ_id": cooperator_account.id,
            }
        )

    def create_company_journal(
        self,
        company: Company,
        name: str,
        type: str,
        code: str,
        account_ref: str,
        product_categ_xml_id: str = False,
    ) -> AccountJournal:
        account = self.env.ref(account_ref.format(company.id))
        journal = self.env["account.journal"].create(
            {
                "name": name,
                "type": type,
                "company_id": company.id,
                "default_account_id": account.id,
                "refund_sequence": True,
                "code": code,
            }
        )
        if product_categ_xml_id:
            self.env.ref(product_categ_xml_id).with_company(company).write(
                {
                    "service_invoicing_sale_journal_id": journal.id,
                    "service_invoicing_purchase_journal_id": journal.id,
                }
            )
        return journal
