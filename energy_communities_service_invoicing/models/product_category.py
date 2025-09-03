from odoo import _, api, fields, models

from odoo.addons.energy_communities.config import (
    PACK_PROD_CATEG_XMLID_REL_TO_PACK_TYPES,
    PACK_TYPE_NONE,
)

from ..config import (
    ASSIGNABLE_PACKS_TO_PARTNER_CATEG_REFS,
    PACK_PRODUCT_PARENT_CATEG_REF,
    SERVICE_PRODUCT_PARENT_CATEG_REF,
    SHARE_PRODUCTS_CATEG_REFS,
)


class ProductCategory(models.Model):
    _name = "product.category"
    _inherit = ["product.category", "pack.type.mixin"]

    is_pack_service = fields.Boolean(
        "Is a pack service", compute="_compute_is_pack_service", store=True
    )
    is_assignable_pack_to_partner = fields.Boolean(
        "Is a pack assignable to partner (via wizard)",
        compute="_compute_is_assignable_pack_to_partner",
        store=True,
    )
    is_config_share = fields.Boolean(
        "Is a share based on config", compute="_compute_is_config_share", store=False
    )
    service_invoicing_sale_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Service invoicing sale journal",
        company_dependent=True,
        help="This journal will be used when creating service invoicing contracts",
    )
    service_invoicing_purchase_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Service invoicing purchase journal",
        company_dependent=True,
        help="This journal will be used when creating service invoicing contracts",
    )
    service_invoicing_sale_team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Service invoicing sales team",
        company_dependent=True,
        help="This sale team will be used when creating service invoicing sale orders",
    )

    @api.depends("data_xml_id")
    def _compute_pack_type(self):
        for record in self:
            record.pack_type = PACK_PROD_CATEG_XMLID_REL_TO_PACK_TYPES.get(
                record.data_xml_id, PACK_TYPE_NONE
            )

    @api.depends("parent_id")
    def _compute_is_pack_service(self):
        for record in self:
            record.is_pack_service = False
            if record.parent_id:
                if record.parent_id.data_xml_id == SERVICE_PRODUCT_PARENT_CATEG_REF:
                    record.is_pack_service = True

    @api.depends("data_xml_id")
    def _compute_is_config_share(self):
        for record in self:
            record.is_config_share = False
            if record.data_xml_id in SHARE_PRODUCTS_CATEG_REFS:
                record.is_config_share = True

    @api.depends("data_xml_id")
    def _compute_is_assignable_pack_to_partner(self):
        for record in self:
            record.is_assignable_pack_to_partner = False
            if record.data_xml_id in ASSIGNABLE_PACKS_TO_PARTNER_CATEG_REFS:
                record.is_assignable_pack_to_partner = True

    def write_with_company(self, company_id, vals):
        self.with_company(company_id).write(vals)
