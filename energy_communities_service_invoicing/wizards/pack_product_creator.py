from odoo import _, api, fields, models

from odoo.addons.energy_communities.utils import (
    _PACK_PRODUCTS_RELATION_TO_SERVICES_REFS,
    get_successful_popup_message,
    product_utils,
)

from ..schemas import (
    PackProductCreationData,
    ProductCreationParams,
    ServiceProductCreationData,
    ServiceProductExistingData,
)


class PackProductCreatorWizard(models.TransientModel):
    _name = "pack.product.creator.wizard"
    _inherit = ["contract.recurrency.basic.mixin"]
    _description = "Assistant for creating a pack product complete configuration"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    pack_categ_id = fields.Many2one("product.category", string="Pack category")
    name = fields.Char(string="Pack name")
    description_sale = fields.Text(string="Sales description")
    default_code = fields.Char(string="Internal Reference")
    list_price = fields.Float(
        "Pack activation price",
        digits="Product Price",
    )
    taxes_id = fields.Many2many(
        "account.tax",
        string="Customer Taxes",
        domain=[("type_tax_use", "=", "sale")],
    )
    service_product_ids = fields.One2many(
        "pack.product.creator.wizard.service.product",
        "pack_product_creator_id",
        string="Included services",
    )
    pack_categ_id_is_config_share = fields.Boolean(
        compute="_compute_pack_categ_id_is_config_share", store=False
    )

    @api.depends("pack_categ_id")
    def _compute_pack_categ_id_is_config_share(self):
        for record in self:
            record.pack_categ_id_is_config_share = record.pack_categ_id.is_config_share

    def execute_create(self):
        result = self._create_products()
        return get_successful_popup_message(
            _("Pack product creation successful"),
            _("Please visit the products view in orde to see the new items."),
        )

    def _create_products(self):
        creation_params = self._build_creation_params()
        with product_utils(self.env) as component:
            return component.create_products(creation_params)

    def _build_creation_params(self):
        new_services = []
        existing_services = []
        for service in self.service_product_ids:
            if service.type == "new":
                new_services.append(
                    ServiceProductCreationData(
                        company_id=self.company_id.id if self.company_id else None,
                        categ_id=self.env.ref(
                            _PACK_PRODUCTS_RELATION_TO_SERVICES_REFS[
                                self.pack_categ_id.data_xml_id
                            ]
                        ).id,
                        name=service.name,
                        description_sale=service.description_sale
                        if service.description_sale
                        else None,
                        default_code=service.default_code
                        if service.default_code
                        else None,
                        list_price=service.list_price,
                        taxes_id=service.taxes_id.ids if service.taxes_id else [],
                        qty_type=service.qty_type,
                        quantity=service.quantity,
                        qty_formula_id=service.qty_formula_id.id
                        if service.qty_formula_id
                        else None,
                    )
                )
            if service.type == "existing":
                existing_services.append(
                    ServiceProductExistingData(
                        product_template_id=service.existing_service_product_id.id,
                        list_price=service.list_price,
                        qty_type=service.qty_type,
                        quantity=service.quantity,
                        qty_formula_id=service.qty_formula_id.id
                        if service.qty_formula_id
                        else None,
                    )
                )
        return ProductCreationParams(
            pack=PackProductCreationData(
                company_id=self.company_id.id if self.company_id else None,
                categ_id=self.pack_categ_id.id,
                name=self.name,
                description_sale=self.description_sale
                if self.description_sale
                else None,
                default_code=self.default_code if self.default_code else None,
                list_price=self.list_price,
                taxes_id=self.taxes_id.ids if self.taxes_id else [],
                recurring_rule_mode=self.recurring_rule_mode,
                recurring_invoicing_type=self.recurring_invoicing_type,
                recurring_interval=self.recurring_interval
                if self.recurring_interval
                else None,
                recurring_rule_type=self.recurring_rule_type
                if self.recurring_rule_type
                else None,
                recurring_invoicing_fixed_type=self.recurring_invoicing_fixed_type
                if self.recurring_invoicing_fixed_type
                else None,
                fixed_invoicing_day=self.fixed_invoicing_day
                if self.fixed_invoicing_day
                else None,
                fixed_invoicing_month=self.fixed_invoicing_month
                if self.fixed_invoicing_month
                else None,
            ),
            new_services=new_services,
            existing_services=existing_services,
        )
