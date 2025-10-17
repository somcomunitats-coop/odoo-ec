# from typing import List
# from odoo import _
# from odoo.exceptions import ValidationError


from odoo.addons.account.models.account_account import AccountAccount
from odoo.addons.account.models.account_journal import AccountJournal
from odoo.addons.base.models.res_company import Company
from odoo.addons.component.core import Component

from ..config import COOP_ACCOUNT_REF_IN_COMPANY


class AccountUtils(Component):
    _inherit = "account.utils"

    def setup_company_cooperator_accounting_configuration(
        self, company: Company
    ) -> None:
        # define company cooperator account
        if self.work.use_sudo:
            company = company.sudo()
        company.write(
            {
                "property_cooperator_account": self.env.ref(
                    COOP_ACCOUNT_REF_IN_COMPANY.format(company.id)
                )
            }
        )
        # define cooperator account in subscription journal
        cooperator_account = company.get_company_coop_account()
        company.subscription_journal_id.write(
            {"default_account_id": cooperator_account.id}
        )
        # create cooperator voluntary account
        self.create_company_account(
            company, "Capital social voluntario", "equity", "100100"
        )

    def create_company_journal(
        self,
        company: Company,
        name: str,
        type: str,
        code: str,
        account_ref: str,
    ) -> AccountJournal:
        account = self.env.ref(account_ref.format(company.id))
        journal_model = self.env["account.journal"]
        if self.work.use_sudo:
            journal_model = journal_model.sudo()
        journal = journal_model.create(
            {
                "name": name,
                "type": type,
                "company_id": company.id,
                "default_account_id": account.id,
                "refund_sequence": True,
                "code": code,
            }
        )
        return journal

    def create_company_account(
        self,
        company: Company,
        name: str,
        account_type: str,
        code: str,
    ) -> AccountAccount:
        account_model = self.env["account.account"]
        if self.work.use_sudo:
            account_model = account_model.sudo()
        return account_model.create(
            {
                "name": name,
                "account_type": account_type,
                "code": code,
                "company_id": company.id,
            }
        )
