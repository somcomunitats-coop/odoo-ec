import logging

from odoo import models

from odoo.addons.component.exception import RegistryNotReadyError
from odoo.addons.energy_communities.utils import account_utils, product_utils

from ..config import (
    SELFCONSUMPTION_ACCOUNT_REF,
    SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
)

_logger = logging.getLogger(__name__)

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
                    SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
                )
            with product_utils(self.env) as product_component:
                # create company pricelist
                product_component.create_company_pricelist(self.new_company_id)
                product_component.setup_company_product_categs(self.new_company_id)
        except Exception as e:
            if isinstance(e, RegistryNotReadyError):
                _logger.warning(
                    "Avoiding company pricelist if component registry not initialized"
                )
            else:
                raise (e)

