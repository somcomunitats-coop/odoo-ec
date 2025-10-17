from typing import List

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.account.models.account_account import AccountAccount
from odoo.addons.base.models.res_company import Company
from odoo.addons.component.core import Component
from odoo.addons.contract.models.contract_template import ContractTemplate
from odoo.addons.energy_communities.models.res_company import (
    _LEGAL_FORM_VALUES_NON_PROFIT,
)
from odoo.addons.energy_communities_cooperator.config import (
    COOP_SHARE_PRODUCT_CATEG_REF,
    COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
)
from odoo.addons.product.models.product_pricelist import Pricelist
from odoo.addons.product.models.product_template import ProductTemplate

from ..config import (
    COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
    PLATFORM_ACCOUNT_REF,
    PLATFORM_ACCOUNT_REF_EXPENSE,
    PLATFORM_PACK_PRODUCT_CATEG_REF,
    PLATFORM_SERVICE_PRODUCT_CATEG_REF,
    RECURRING_FEE_ACCOUNT_REF,
    RECURRING_FEE_ACCOUNT_REF_EXPENSE,
    RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
    RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
    SELFCONSUMPTION_ACCOUNT_REF,
    SELFCONSUMPTION_ACCOUNT_REF_EXPENSE,
    SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
    SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF,
    SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
)
from ..schemas import (
    BaseProductCreationData,
    PackProductCreationData,
    ProductCreationParams,
    ProductCreationResult,
    ServiceProductCreationData,
    ServiceProductExistingData,
)


class ProductUtils(Component):
    _inherit = "product.utils"

    def create_product(
        self,
        product_creation_params: ServiceProductCreationData,
        apply_on_pricelist: bool = False,
    ) -> ProductTemplate:
        self._validate_service_configuration(product_creation_params)
        new_product = self._create_base_product(
            BaseProductCreationData(
                company_id=product_creation_params.company_id,
                categ_id=product_creation_params.categ_id,
                name=product_creation_params.name,
                description_sale=product_creation_params.description_sale,
                default_code=product_creation_params.default_code,
                list_price=product_creation_params.list_price,
                taxes_id=product_creation_params.taxes_id,
                short_name=product_creation_params.short_name,
                sale_ok=product_creation_params.sale_ok,
                purchase_ok=product_creation_params.purchase_ok,
                display_on_website=product_creation_params.display_on_website,
                default_share_product=product_creation_params.default_share_product,
            )
        )
        if apply_on_pricelist:
            self._apply_services_on_system_pricelist([new_product])
        return new_product

    def create_products(
        self,
        product_creation_params: ProductCreationParams,
    ) -> ProductCreationResult:
        pack_product_template = False
        new_service_product_template_list = []
        existing_service_product_template_list = []
        # CREATE SERVICE PRODUCTS
        if product_creation_params.new_services:
            for service_product_creation_data in product_creation_params.new_services:
                new_service_product_template_list.append(
                    self.create_product(service_product_creation_data)
                )
        # EXISTING SERVICE PRODUCTS
        if product_creation_params.existing_services:
            existing_service_product_template_list = list(
                map(
                    lambda existing_data: self.env["product.template"].browse(
                        existing_data.product_template_id
                    ),
                    product_creation_params.existing_services,
                )
            )
        # CREATE PACK PRODUCT
        if product_creation_params.pack:
            self._apply_services_on_system_pricelist(
                new_service_product_template_list
                + existing_service_product_template_list
            )
            pack_product_template = self._create_pack_product(
                product_creation_params,
                new_service_product_template_list,
                existing_service_product_template_list,
            )
        # RETURN RESULT
        return ProductCreationResult(
            pack_product_template=pack_product_template,
            new_service_product_template_list=new_service_product_template_list,
            existing_service_product_template_list=existing_service_product_template_list,
        )

    def create_company_pricelist(self, company: Company) -> Pricelist:
        # validate pricelist creation
        if company.pricelist_id:
            raise ValidationError("A company pricelist already exists")
        # create company pricelist
        pricelist_model = self.env["product.pricelist"]
        if self.work.use_sudo:
            pricelist_model = pricelist_model.sudo()
            company = company.sudo()
        company_pricelist = pricelist_model.create(
            {
                "name": "{} pricelist".format(company.name),
                "currency_id": self.env.ref("base.EUR").id,
                "company_id": company.id,
            }
        )
        company.write({"pricelist_id": company_pricelist.id})
        return company_pricelist

    def setup_company_product_categs(self, company: Company) -> None:
        self._setup_company_product_categs_saleteam(company)
        self._setup_company_product_categs_journal(company)
        self._setup_company_product_categs_accounts(company)

    def _setup_company_product_categs_saleteam(self, company: Company) -> None:
        self._setup_company_product_categ_saleteam(
            company, COOP_SHARE_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, PLATFORM_PACK_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, RECURRING_FEE_PACK_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, PLATFORM_SERVICE_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF
        )
        self._setup_company_product_categ_saleteam(
            company, SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF
        )

    def _setup_company_product_categ_saleteam(
        self, company: Company, categ_ref: str
    ) -> None:
        sale_team_model = self.env["crm.team"]
        if self.work.use_sudo:
            sale_team_model = sale_team_model.sudo()
        default_sale_team = sale_team_model.search(
            [
                ("company_id", "=", company.id),
                ("is_default_team", "=", True),
            ],
            limit=1,
        )
        if default_sale_team:
            categ_model = self.env.ref(categ_ref).with_company(company)
            if self.work.use_sudo:
                categ_model = categ_model.sudo()
            categ_model.write(
                {
                    "service_invoicing_sale_team_id": default_sale_team.id,
                }
            )

    def _setup_company_product_categs_journal(self, company: Company) -> None:
        acc_journal_model = self.env["account.journal"]
        if self.work.use_sudo:
            acc_journal_model = acc_journal_model.sudo()
        afc_journal = acc_journal_model.search(
            [("company_id", "=", company.id), ("code", "=", "AFC")], limit=1
        )
        self._setup_company_product_categ_journal(
            company, COOP_SHARE_PRODUCT_CATEG_REF, False
        )
        self._setup_company_product_categ_journal(
            company, COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF, False
        )
        self._setup_company_product_categ_journal(
            company, COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF, False
        )
        self._setup_company_product_categ_journal(
            company, PLATFORM_PACK_PRODUCT_CATEG_REF, False
        )
        self._setup_company_product_categ_journal(
            company, RECURRING_FEE_PACK_PRODUCT_CATEG_REF, False
        )
        self._setup_company_product_categ_journal(
            company, SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF, afc_journal
        )
        self._setup_company_product_categ_journal(
            company, PLATFORM_SERVICE_PRODUCT_CATEG_REF, False
        )
        self._setup_company_product_categ_journal(
            company, RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF, False
        )
        self._setup_company_product_categ_journal(
            company,
            SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
            company.subscription_journal_id,
        )
        self._setup_company_product_categ_journal(
            company, SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF, afc_journal
        )

    def _setup_company_product_categ_journal(self, company, categ_ref, journal) -> None:
        if journal:
            categ_model = self.env.ref(categ_ref)
            if self.work.use_sudo:
                categ_model = categ_model.sudo()
            categ_model.with_company(company).write(
                {"service_invoicing_sale_journal_id": journal.id}
            )

    def _setup_company_product_categs_accounts(self, company: Company) -> None:
        # coop share product categ
        cooperator_account = company.get_company_coop_account()
        self._setup_company_product_categ_accounts(
            company,
            COOP_SHARE_PRODUCT_CATEG_REF,
            cooperator_account,
            cooperator_account,
        )
        # voluntary share product categ
        account_model = self.env["account.account"]
        if self.work.use_sudo:
            account_model = account_model.sudo()
        coop_voluntary_account = account_model.search(
            [("company_id", "=", company.id), ("code", "=", "100100")]
        )
        self._setup_company_product_categ_accounts(
            company,
            COOP_VOLUNTARY_SHARE_PRODUCT_CATEG_REF,
            coop_voluntary_account,
            coop_voluntary_account,
        )
        # platform pack product categ
        self._setup_company_product_categ_accounts(
            company,
            PLATFORM_PACK_PRODUCT_CATEG_REF,
            self.env.ref(PLATFORM_ACCOUNT_REF.format(company.id)),
            self.env.ref(PLATFORM_ACCOUNT_REF_EXPENSE.format(company.id)),
        )
        # share recurring fee pack
        if company.legal_form in _LEGAL_FORM_VALUES_NON_PROFIT:
            self._setup_company_product_categ_accounts(
                company,
                COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
                cooperator_account,
                cooperator_account,
            )
        else:
            self._setup_company_product_categ_accounts(
                company,
                COOP_SHARE_RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
            )
        # recurring fee pack
        self._setup_company_product_categ_accounts(
            company,
            RECURRING_FEE_PACK_PRODUCT_CATEG_REF,
            self.env.ref(RECURRING_FEE_ACCOUNT_REF.format(company.id)),
            self.env.ref(RECURRING_FEE_ACCOUNT_REF_EXPENSE.format(company.id)),
        )
        # selfconsumption pack
        self._setup_company_product_categ_accounts(
            company,
            SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
            self.env.ref(SELFCONSUMPTION_ACCOUNT_REF.format(company.id)),
            self.env.ref(SELFCONSUMPTION_ACCOUNT_REF_EXPENSE.format(company.id)),
        )
        # platform service product categ
        self._setup_company_product_categ_accounts(
            company,
            PLATFORM_SERVICE_PRODUCT_CATEG_REF,
            self.env.ref(PLATFORM_ACCOUNT_REF.format(company.id)),
            self.env.ref(PLATFORM_ACCOUNT_REF_EXPENSE.format(company.id)),
        )
        # share recurring fee service
        share_recurring_fee_account = (
            company.get_company_share_recurring_fee_service_account()
        )
        self._setup_company_product_categ_accounts(
            company,
            SHARE_RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
            share_recurring_fee_account,
            share_recurring_fee_account,
        )
        # recurring fee service
        self._setup_company_product_categ_accounts(
            company,
            RECURRING_FEE_SERVICE_PRODUCT_CATEG_REF,
            self.env.ref(RECURRING_FEE_ACCOUNT_REF.format(company.id)),
            self.env.ref(RECURRING_FEE_ACCOUNT_REF_EXPENSE.format(company.id)),
        )
        # selfconsumption service
        self._setup_company_product_categ_accounts(
            company,
            SELFCONSUMPTION_SERVICE_PRODUCT_CATEG_REF,
            self.env.ref(SELFCONSUMPTION_ACCOUNT_REF.format(company.id)),
            self.env.ref(SELFCONSUMPTION_ACCOUNT_REF_EXPENSE.format(company.id)),
        )

    def _setup_company_product_categ_accounts(
        self,
        company: Company,
        categ_ref: str,
        income_account: AccountAccount = False,
        expense_account: AccountAccount = False,
    ) -> None:
        categ_model = self.env.ref(categ_ref).with_company(company)
        if self.work.use_sudo:
            categ_model = categ_model.sudo()
        categ_model.write(
            {
                "property_account_income_categ_id": income_account.id
                if income_account
                else False,
                "property_account_expense_categ_id": expense_account.id
                if expense_account
                else False,
            }
        )

    def _validate_service_configuration(
        self, service_product_creation_data: ServiceProductCreationData
    ) -> None:
        if service_product_creation_data.company_id:
            company = self.env["res.company"].browse(
                service_product_creation_data.company_id
            )
            if not company.pricelist_id:
                raise ValidationError(
                    _(
                        "Before creating services you must create and configure a Tariff model for this company"
                    )
                )

    def _apply_services_on_system_pricelist(
        self, service_product_template_list: List[ProductTemplate]
    ):
        if service_product_template_list:
            if service_product_template_list[0].company_id:
                pricelist = service_product_template_list[0].company_id.pricelist_id
            else:
                pricelist = self.env.ref("product.list0")
            for service_product_template in service_product_template_list:
                pricelist_item_model = self.env["product.pricelist.item"]
                if self.work.use_sudo:
                    pricelist_item_model = pricelist_item_model.sudo()
                pricelist_item_model.create(
                    {
                        "product_tmpl_id": service_product_template.id,
                        "fixed_price": service_product_template.list_price,
                        "pricelist_id": pricelist.id,
                    }
                )

    def _create_pack_product(
        self,
        product_creation_params: ProductCreationParams,
        new_service_product_template_list: List[ProductTemplate] = False,
        existing_service_product_template_list: List[ProductTemplate] = False,
    ) -> ProductTemplate:
        # BASE PACK PRODUCT
        pack_product = self._create_base_product(
            BaseProductCreationData(
                company_id=product_creation_params.pack.company_id,
                categ_id=product_creation_params.pack.categ_id,
                name=product_creation_params.pack.name,
                description_sale=product_creation_params.pack.description_sale,
                default_code=product_creation_params.pack.default_code,
                list_price=product_creation_params.pack.list_price,
                taxes_id=product_creation_params.pack.taxes_id,
                short_name=product_creation_params.pack.short_name,
                sale_ok=product_creation_params.pack.sale_ok,
                purchase_ok=product_creation_params.pack.purchase_ok,
                display_on_website=product_creation_params.pack.display_on_website,
                default_share_product=product_creation_params.pack.default_share_product,
            )
        )
        # CONTRACT TEMPLATE
        self._create_pack_contract_template(
            product_creation_params,
            pack_product,
            new_service_product_template_list,
            existing_service_product_template_list,
        )
        return pack_product

    def _create_base_product(
        self, product_creation_data: BaseProductCreationData
    ) -> ProductTemplate:
        creation_dict = product_creation_data.model_dump() | {
            "detailed_type": "service",
            "invoice_policy": "order",
        }
        if not creation_dict["short_name"]:
            creation_dict["short_name"] = creation_dict["name"]
        product_model = self.env["product.template"]
        if self.work.use_sudo:
            product_model = product_model.sudo()
        product = product_model.create(creation_dict)
        self._apply_special_flags_to_product(product)
        return product

    def _apply_special_flags_to_product(self, product: ProductTemplate) -> bool:
        special_flags = {}
        if product.is_config_share:
            special_flags["is_share"] = True
            special_flags["by_company"] = True
            special_flags["by_individual"] = True
        if product.is_pack:
            special_flags["is_contract"] = True
        if special_flags:
            if self.work.use_sudo:
                product = product.sudo()
            product.write(special_flags)
            return True
        return False

    def _create_pack_contract_template(
        self,
        product_creation_params: ProductCreationParams,
        pack_product: ProductTemplate,
        new_service_product_template_list: List[ProductTemplate] = False,
        existing_service_product_template_list: List[ProductTemplate] = False,
    ) -> None:
        creation_data = {
            "name": "[TEMPLATE] {}".format(pack_product.name),
            "company_id": pack_product.company_id.id
            if pack_product.company_id
            else None,
            "contract_line_ids": [],
        }
        creation_data[
            "contract_line_ids"
        ] += self._build_contract_template_lines_creation_data(
            product_creation_params.pack,
            product_creation_params.new_services,
            new_service_product_template_list,
        )
        creation_data[
            "contract_line_ids"
        ] += self._build_contract_template_lines_creation_data(
            product_creation_params.pack,
            product_creation_params.existing_services,
            existing_service_product_template_list,
        )
        contract_template_model = self.env["contract.template"]
        if self.work.use_sudo:
            contract_template_model = contract_template_model.sudo()
            pack_product = pack_product.sudo()
        contract_template = contract_template_model.create(creation_data)
        pack_product.write({"property_contract_template_id": contract_template.id})

    def _build_contract_template_lines_creation_data(
        self,
        pack_product_data: PackProductCreationData,
        service_product_data_list: List[ServiceProductCreationData]
        | List[ServiceProductExistingData],
        service_product_template_list: List[ProductTemplate],
    ) -> list:
        lines = []
        if service_product_data_list and service_product_template_list:
            for i in range(0, len(service_product_template_list)):
                lines.append(
                    (
                        0,
                        0,
                        self._build_contract_template_line_creation_data(
                            pack_product_data,
                            service_product_data_list[i],
                            service_product_template_list[i],
                        ),
                    )
                )
        return lines

    def _build_contract_template_line_creation_data(
        self,
        pack_product_data: PackProductCreationData,
        service_product_data: ServiceProductCreationData | ServiceProductExistingData,
        service_product_template: ProductTemplate,
    ) -> dict:
        creation_data_item = {
            "product_id": service_product_template.product_variant_id.id,
            "automatic_price": True,
            "qty_type": service_product_data.qty_type,
            "qty_formula_id": service_product_data.qty_formula_id,
            "quantity": service_product_data.quantity,
            "name": service_product_template.description_sale
            if service_product_template.description_sale
            else service_product_template.name,
            "recurring_rule_mode": pack_product_data.recurring_rule_mode,
            "recurring_invoicing_type": pack_product_data.recurring_invoicing_type,
            "recurring_invoicing_fixed_type": pack_product_data.recurring_invoicing_fixed_type,
            "fixed_invoicing_day": pack_product_data.fixed_invoicing_day,
            "fixed_invoicing_month": pack_product_data.fixed_invoicing_month,
        }
        if pack_product_data.recurring_interval:
            creation_data_item[
                "recurring_interval"
            ] = pack_product_data.recurring_interval
        if pack_product_data.recurring_interval:
            creation_data_item[
                "recurring_rule_type"
            ] = pack_product_data.recurring_rule_type
        return creation_data_item
