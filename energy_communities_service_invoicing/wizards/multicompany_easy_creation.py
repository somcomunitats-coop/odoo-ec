import logging

from odoo import _, api, fields, models

from odoo.addons.component.exception import RegistryNotReadyError
from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_NON_PROFIT,
)
from odoo.addons.energy_communities.utils import product_utils

_logger = logging.getLogger(__name__)


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = [
        "account.multicompany.easy.creation.wiz",
        "contract.recurrency.basic.mixin",
    ]

    def thread_action_accept(self):
        super().thread_action_accept()
        self._create_default_pricelist()
        self._setup_cooperator_account()

    def _setup_cooperator_account(self):
        # select cooperator account to be used
        if self.new_company_id.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            cooperator_account = self.env.ref(
                "l10n_es.{}_account_assoc_720".format(self.new_company_id.id)
            )
        else:
            cooperator_account = self.env.ref(
                "l10n_es.{}_account_pymes_100".format(self.new_company_id.id)
            )
        # define company cooperator account
        self.new_company_id.write(
            {
                "property_cooperator_account": self.env.ref(
                    "l10n_es.{}_account_common_4400".format(self.new_company_id.id)
                )
            }
        )
        # move to cooperator journal
        self.new_company_id.subscription_journal_id.write(
            {"default_account_id": cooperator_account.id}
        )
        # move to product category
        self.env.ref("cooperator.product_category_company_share").with_company(
            self.new_company_id
        ).write(
            {
                "service_invoicing_sale_journal_id": self.new_company_id.subscription_journal_id.id,
                "service_invoicing_purchase_journal_id": self.new_company_id.subscription_journal_id.id,
                "property_account_income_categ_id": cooperator_account.id,
                "property_account_expense_categ_id": cooperator_account.id,
            }
        )

    def _create_default_pricelist(self):
        # Using try exception to avoid component usage on demo data load
        try:
            with product_utils(self.env) as component:
                return component.create_company_pricelist(self.new_company_id)
        except Exception as e:
            if isinstance(e, RegistryNotReadyError):
                _logger.warning(
                    "Avoiding company pricelist if component registry not initialized"
                )
            else:
                raise (e)
