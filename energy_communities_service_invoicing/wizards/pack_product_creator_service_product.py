from odoo import _, api, fields, models

from odoo.addons.energy_communities.config import (
    PACK_PROD_CATEG_XMLID_REL_TO_SERVICE_PROD_CATEG_XMLID,
)


class PackProductCreatorWizardServiceProduct(models.TransientModel):
    _name = "pack.product.creator.wizard.service.product"
    _description = "A service configuration included on a pack"

    type = fields.Selection(
        [("new", _("New Service")), ("existing", _("Existing Service"))],
        string="Creation type",
        default="new",
    )
    name = fields.Char(string="Name")
    pack_product_creator_id = fields.Many2one("pack.product.creator.wizard")
    description_sale = fields.Text(string="Sales description")
    default_code = fields.Char(string="Internal Reference")
    list_price = fields.Float(
        "Service price",
        digits="Product Price",
    )
    quantity = fields.Float(default=1.0, string="Quantity")
    qty_type = fields.Selection(
        selection=[("fixed", "Fixed quantity"), ("variable", "Variable quantity")],
        default="fixed",
        string="Quantity type",
    )
    qty_formula_id = fields.Many2one(
        comodel_name="contract.line.qty.formula", string="Quantity formula"
    )
    taxes_id = fields.Many2many(
        "account.tax",
        string="Customer Taxes",
        domain=[("type_tax_use", "=", "sale")],
    )
    existing_service_product_id = fields.Many2one(
        comodel_name="product.template", string="Existing service product"
    )
    allowed_service_product_categ_id = fields.Integer(
        string="Allowed service product categ id",
        compute="_compute_allowed_service_product_categ_id",
        store=False,
    )
    allowed_service_product_company_id = fields.Integer(
        string="Allowed service product company id",
        compute="_compute_allowed_service_product_company_id",
        store=False,
    )
    allowed_service_product_ids = fields.Many2many(
        "product.template",
        string="Allowed service product domain",
        compute="_compute_allowed_service_product_ids",
        store=False,
    )

    @api.depends("pack_product_creator_id")
    def _compute_allowed_service_product_categ_id(self):
        for record in self:
            record.allowed_service_product_categ_id = 0
            if record.pack_product_creator_id.pack_categ_id:
                record.allowed_service_product_categ_id = self.env.ref(
                    PACK_PROD_CATEG_XMLID_REL_TO_SERVICE_PROD_CATEG_XMLID[
                        record.pack_product_creator_id.pack_categ_id.data_xml_id
                    ]
                ).id

    @api.depends("pack_product_creator_id")
    def _compute_allowed_service_product_company_id(self):
        for record in self:
            record.allowed_service_product_company_id = False
            if record.pack_product_creator_id.company_id:
                record.allowed_service_product_company_id = (
                    record.pack_product_creator_id.company_id.id
                )

    @api.depends("pack_product_creator_id")
    def _compute_allowed_service_product_ids(self):
        for record in self:
            query = [
                ("is_pack_service", "=", True),
                ("categ_id", "=", self.allowed_service_product_categ_id),
            ]
            if bool(self.allowed_service_product_company_id):
                query.append(
                    ("company_id", "=", self.allowed_service_product_company_id)
                )
            else:
                query.append(("company_id", "=", False))
            record.allowed_service_product_ids = (
                self.env["product.template"].search(query).ids
            )
