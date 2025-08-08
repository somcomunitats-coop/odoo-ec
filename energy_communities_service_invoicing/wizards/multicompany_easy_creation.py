import logging

from odoo import _, api, fields, models

from odoo.addons.component.exception import RegistryNotReadyError
from odoo.addons.energy_communities.config import (
    PACK_TYPE_SELFCONSUMPTION_PROD_CATEG_XMLID,
)
from odoo.addons.energy_communities.utils import account_utils, product_utils

from ..config import (
    COOP_ACCOUNT_REF_GENERAL,
    COOP_ACCOUNT_REF_IN_COMPANY,
    COOP_ACCOUNT_REF_NONPROFIT,
    COOP_SHARE_PRODUCT_CATEG_REF,
    SELFCONSUMPTION_ACCOUNT_REF,
)

_logger = logging.getLogger(__name__)


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = [
        "account.multicompany.easy.creation.wiz",
        "contract.recurrency.basic.mixin",
    ]

    def thread_action_accept(self):
        super().thread_action_accept()
        # Using try exception to avoid component usage on demo data load
        try:
            with account_utils(self.env) as account_component:
                # setup company cooperator account
                account_component.setup_company_cooperator_accounting_configuration(
                    self.new_company_id
                )
                # create company selfconsumption journal
                account_component.create_company_journal(
                    self.new_company_id,
                    "Autoconsumo Fotovoltaico Compartido",
                    "sale",
                    "AFC",
                    SELFCONSUMPTION_ACCOUNT_REF,
                    PACK_TYPE_SELFCONSUMPTION_PROD_CATEG_XMLID,
                )
            with product_utils(self.env) as product_component:
                # create company pricelist
                product_component.create_company_pricelist(self.new_company_id)
        except Exception as e:
            if isinstance(e, RegistryNotReadyError):
                _logger.warning(
                    "Avoiding company pricelist if component registry not initialized"
                )
            else:
                raise (e)
