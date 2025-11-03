# from typing import List
# from odoo.exceptions import ValidationError


from odoo import _

from odoo.addons.account.models.account_account import AccountAccount
from odoo.addons.account.models.account_journal import AccountJournal
from odoo.addons.account.models.res_partner_bank import ResPartnerBank
from odoo.addons.base.models.res_company import Company
from odoo.addons.component.core import Component

from ..config import COOP_ACCOUNT_REF_IN_COMPANY


class AccountUtils(Component):
    _inherit = "account.utils"

    def setup_company_cooperator_account(self, company: Company) -> None:
        if self.work.use_sudo:
            company = company.sudo()
        company.write(
            {
                "property_cooperator_account": self.env.ref(
                    COOP_ACCOUNT_REF_IN_COMPANY.format(company.id)
                )
            }
        )

    def setup_journal_default_account(
        self, journal: AccountJournal, account: AccountAccount
    ) -> None:
        if self.work.use_sudo:
            journal = journal.sudo()
            account = account.sudo()
        journal.write({"default_account_id": account.id})

    def create_company_res_partner_bank_account(
        self,
        company: Company,
        acc_number: str,
        allow_out_payment: bool,
    ) -> ResPartnerBank:
        res_partner_bank_model = self.env["res.partner.bank"]
        if self.work.use_sudo:
            res_partner_bank_model = res_partner_bank_model.sudo()
        return res_partner_bank_model.create(
            {
                "acc_number": acc_number,
                "partner_id": company.partner_id.id,
                "company_id": company.id,
                "allow_out_payment": allow_out_payment,
            }
        )

    def create_company_journal(
        self,
        company: Company,
        name: str,
        type: str,
        code: str,
        account: AccountAccount,
    ) -> AccountJournal:
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

    def get_bank_journal_name(
        self,
        res_partner_bank: AccountAccount,
    ):
        name_prefix = _("Bank")
        if res_partner_bank.bank_id:
            name_prefix = res_partner_bank.bank_id.name
        return "{name_prefix} ({acc_number_min})".format(
            name_prefix=name_prefix, acc_number_min=res_partner_bank.acc_number[-4:]
        )

    def create_company_bank_journal(
        self,
        company: Company,
        res_partner_bank: AccountAccount,
    ) -> None:
        # define name to be used on models
        models_name = self.get_bank_journal_name(res_partner_bank)
        # use sudo if necessary
        account_model = self.env["account.account"]
        journal_model = self.env["account.journal"]
        if self.work.use_sudo:
            account_model = account_model.sudo()
            journal_model = journal_model.sudo()
        # create account journal
        accounts_type_bank = account_model.search(
            [("code", "like", "572%"), ("company_id", "=", company.id)]
        )
        journal_account = self.create_company_account(
            company, models_name, "asset_cash", f"57200{len(accounts_type_bank)}"
        )
        # create bank journal
        journal = self.create_company_journal(
            company,
            models_name,
            "bank",
            journal_model.get_next_bank_cash_default_code("bank", company),
            journal_account,
        )
        # add res_partner_bank to journal
        if self.work.use_sudo:
            journal = journal.sudo()
        journal.write({"bank_account_id": res_partner_bank.id})

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
