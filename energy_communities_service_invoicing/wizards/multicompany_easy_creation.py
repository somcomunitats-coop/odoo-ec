import logging

from odoo import _, api, fields, models

from odoo.addons.component.exception import RegistryNotReadyError
from odoo.addons.energy_communities.utils import account_utils, product_utils
from odoo.addons.energy_communities_cooperator.config import (
    COOP_SHARE_PRODUCT_CATEG_REF,
    COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
)

from ..config import (
    COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
    SELFCONSUMPTION_ACCOUNT_REF,
    SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
    SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
    VSIR_ACCOUNT_REF,
)
from ..schemas import (
    PackProductCreationData,
    ProductCreationParams,
    ServiceProductCreationData,
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
            with account_utils(self.env, use_sudo=True) as account_component:
                # setup company cooperator account
                account_component.setup_company_cooperator_accounting_configuration(
                    company=self.new_company_id
                )
                # create company selfconsumption journal
                if self.new_company_id.hierarchy_level == "community":
                    account_component.create_company_journal(
                        self.new_company_id,
                        "Autoconsumo Fotovoltaico Compartido",
                        "sale",
                        "AFC",
                        SELFCONSUMPTION_ACCOUNT_REF,
                    )
                # create vsir journal for cooperatives
                if self.new_company_id.legal_form == "cooperative":
                    vsir_journal = account_component.create_company_journal(
                        self.new_company_id,
                        "Intereses de aportaciones Voluntarias",
                        "purchase",
                        "VSIR",
                        VSIR_ACCOUNT_REF,
                    )
                    self.new_company_id.write(
                        {"voluntary_share_journal_account": vsir_journal.id}
                    )
            with product_utils(self.env, use_sudo=True) as product_component:
                # create company pricelist
                product_component.create_company_pricelist(self.new_company_id)
                product_component.setup_company_product_categs(self.new_company_id)
                # coop product
                if self.new_company_id.legal_form in ["cooperative", "undefined"]:
                    coop_product = product_component.create_product(
                        self._coop_product_creation_params()
                    )
                    self._coop_product_translations(coop_product)
                    vol_coop_product = product_component.create_product(
                        self._vol_coop_product_creation_params()
                    )
                    self._vol_coop_product_translations(vol_coop_product)
                    self.new_company_id.write(
                        {"voluntary_share_id": vol_coop_product.id}
                    )
                # nonprofit share recuring fee product
                if (
                    self.new_company_id.legal_form == "non_profit"
                    and self.fixed_invoicing_day
                    and self.fixed_invoicing_month
                ):
                    share_pack_creation_result = product_component.create_products(
                        self._share_recurring_fee_pack_creation_params()
                    )
                    self._share_recurring_fee_pack_translations(
                        share_pack_creation_result
                    )
                # non profit coop product
                if self.new_company_id.legal_form == "non_profit" and (
                    not self.fixed_invoicing_day or not self.fixed_invoicing_month
                ):
                    coop_product = product_component.create_product(
                        self._nonprofit_share_product_creation_params()
                    )
                    self._nonprofit_share_product_translations(coop_product)
        except Exception as e:
            if isinstance(e, RegistryNotReadyError):
                _logger.warning(
                    "Avoiding company pricelist if component registry not initialized"
                )
            else:
                raise (e)

    def _coop_product_creation_params(self):
        return ServiceProductCreationData(
            company_id=self.new_company_id.id,
            categ_id=self.env.ref(COOP_SHARE_PRODUCT_CATEG_REF).id,
            name="Aportación obligatoria al capital social",
            description_sale=None,
            default_code="CS",
            list_price=self.capital_share,
            taxes_id=[],
            short_name="Capital social",
            sale_ok=False,
            display_on_website=True,
            default_share_product=True,
        )

    def _coop_product_translations(self, coop_product):
        coop_product.with_context(lang="ca_ES").write(
            {"name": "Aportació obligatòria al capital social"}
        )
        coop_product.with_context(lang="es_ES").write(
            {"name": "Aportación obligatoria al capital social"}
        )
        coop_product.with_context(lang="eu_ES").write(
            {"name": "Kapital sozialerako nahitaezko ekarpena"}
        )

    def _vol_coop_product_creation_params(self):
        return ServiceProductCreationData(
            company_id=self.new_company_id.id,
            categ_id=self.env.ref(COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF).id,
            name="Aportación voluntaria al capital social",
            description_sale=None,
            default_code="CSV",
            list_price=10.0,
            taxes_id=[],
            short_name="Capital social voluntario",
            sale_ok=False,
            display_on_website=True,
            default_share_product=False,
        )

    def _vol_coop_product_translations(self, vol_coop_product):
        vol_coop_product.with_context(lang="ca_ES").write(
            {"name": "Aportació voluntària al capital social"}
        )
        vol_coop_product.with_context(lang="es_ES").write(
            {"name": "Aportación voluntaria al capital social"}
        )
        vol_coop_product.with_context(lang="eu_ES").write(
            {"name": "Kapital sozialerako borondatezko ekarpena"}
        )

    def _share_recurring_fee_pack_creation_params(self):
        return ProductCreationParams(
            pack=PackProductCreationData(
                company_id=self.new_company_id.id,
                categ_id=self.env.ref(
                    COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF
                ).id,
                name="Cuota inicial afiliación socia",
                description_sale="Cuota inicial afiliación socia",
                default_code="CIAS",
                list_price=self.capital_share,
                taxes_id=[],
                short_name="Cuota inicial afiliación",
                sale_ok=True,
                purchase_ok=True,
                display_on_website=True,
                default_share_product=True,
                recurring_rule_mode="fixed",
                recurring_invoicing_type="pre-paid",
                recurring_interval=None,
                recurring_rule_type=None,
                recurring_invoicing_fixed_type="yearly",
                fixed_invoicing_day=self.fixed_invoicing_day,
                fixed_invoicing_month=self.fixed_invoicing_month,
            ),
            new_services=[
                ServiceProductCreationData(
                    company_id=self.new_company_id.id,
                    categ_id=self.env.ref(
                        SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
                    ).id,
                    name="Cuota anual afiliación socia",
                    description_sale="Cuota anual afiliación",
                    default_code="CAAS",
                    list_price=self.capital_share,
                    taxes_id=[],
                    short_name="Cuota anual afiliación",
                    sale_ok=True,
                    purchase_ok=True,
                    display_on_website=False,
                    default_share_product=False,
                    qty_type="fixed",
                    quantity=1,
                )
            ],
        )

    def _share_recurring_fee_pack_translations(self, creation_results):
        creation_results.pack_product_template.with_context(lang="ca_ES").write(
            {
                "name": "Cuota inicial afiliació sòcia",
                "description_sale": "Cuota inicial afiliació sòcia",
            }
        )
        creation_results.pack_product_template.with_context(lang="es_ES").write(
            {
                "name": "Cuota inicial afiliación socia",
                "description_sale": "Cuota inicial afiliación socia",
            }
        )
        creation_results.pack_product_template.with_context(lang="eu_ES").write(
            {
                "name": "Bazkide afiliazioaren hasierako kuota",
                "description_sale": "Bazkide afiliazioaren hasierako kuota",
            }
        )
        creation_results.new_service_product_template_list[0].with_context(
            lang="ca_ES"
        ).write(
            {
                "name": "Cuota annual afiliació sòcia",
                "description_sale": "Cuota annual afiliació sòcia",
            }
        )
        creation_results.new_service_product_template_list[0].with_context(
            lang="es_ES"
        ).write(
            {
                "name": "Cuota anual afiliación socia",
                "description_sale": "Cuota anual afiliación socia",
            }
        )
        creation_results.new_service_product_template_list[0].with_context(
            lang="eu_ES"
        ).write(
            {
                "name": "Bazkide afiliazioaren urteko kuota",
                "description_sale": "Bazkide afiliazioaren urteko kuota",
            }
        )

    def _nonprofit_share_product_creation_params(self):
        return ServiceProductCreationData(
            company_id=self.new_company_id.id,
            categ_id=self.env.ref(COOP_SHARE_PRODUCT_CATEG_REF).id,
            name="Cuota inicial afiliación socia",
            description_sale=None,
            default_code="CIA",
            list_price=self.capital_share,
            taxes_id=[],
            short_name="Cuota inicial afiliación",
            sale_ok=False,
            purchase_ok=False,
            display_on_website=True,
            default_share_product=True,
        )

    def _nonprofit_share_product_translations(self, coop_product):
        coop_product.with_context(lang="ca_ES").write(
            {
                "name": "Cuota inicial afiliació sòcia",
            }
        )
        coop_product.with_context(lang="es_ES").write(
            {
                "name": "Cuota inicial afiliación socia",
            }
        )
        coop_product.with_context(lang="eu_ES").write(
            {
                "name": "Bazkide afiliazioaren hasierako kuota",
            }
        )
