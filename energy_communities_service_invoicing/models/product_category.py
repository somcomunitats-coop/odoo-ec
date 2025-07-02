from odoo import _, api, fields, models

from ..utils import (
    _PACK_PRODUCT_PARENT_CATEG_REF,
    _SERVICE_PRODUCT_PARENT_CATEG_REF,
    _SHARE_PRODUCTS_CATEG_REFS,
)


class ProductCategory(models.Model):
    _name = "product.category"
    _inherit = "product.category"

    is_pack = fields.Boolean(
        "Is a pack category", compute="_compute_is_pack", store=True
    )
    is_service = fields.Boolean(
        "Is a service category", compute="_compute_is_service", store=True
    )
    is_config_share = fields.Boolean(
        "Is a shared based on config", compute="_compute_is_config_share", store=False
    )
    data_xml_id = fields.Char("XML ID", compute="_compute_data_xml_id", store=True)
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

    @api.depends("parent_id")
    def _compute_is_pack(self):
        for record in self:
            record.is_pack = False
            if record.parent_id:
                if record.parent_id.data_xml_id == _PACK_PRODUCT_PARENT_CATEG_REF:
                    record.is_pack = True

    @api.depends("parent_id")
    def _compute_is_service(self):
        for record in self:
            record.is_service = False
            if record.parent_id:
                if record.parent_id.data_xml_id == _SERVICE_PRODUCT_PARENT_CATEG_REF:
                    record.is_service = True

    @api.depends("data_xml_id")
    def _compute_is_config_share(self):
        for record in self:
            record.is_config_share = False
            if record.data_xml_id in _SHARE_PRODUCTS_CATEG_REFS:
                record.is_config_share = True

    def _compute_data_xml_id(self):
        for record in self:
            res = record.get_external_id()
            record.data_xml_id = False
            if res.get(record.id):
                record.data_xml_id = res.get(record.id)
