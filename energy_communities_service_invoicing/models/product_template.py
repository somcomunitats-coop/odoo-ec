from odoo import api, fields, models

from odoo.addons.energy_communities.config import PACK_TYPE_NONE


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "pack.type.mixin"]

    property_contract_template_id = fields.Many2one(
        company_dependent=False,
    )
    related_contract_product_ids = fields.One2many(
        "product.product",
        string="Related services",
        compute="_compute_related_contract_product_ids",
        store=False,
    )
    is_config_share = fields.Boolean(
        "Is a shared based on config", compute="_compute_is_config_share", store=False
    )
    is_assignable_pack_to_partner = fields.Boolean(
        "Is a pack assignable to partner (via wizard)",
        related="categ_id.is_assignable_pack_to_partner",
    )
    is_pack_service = fields.Boolean(
        "Is a pack service", related="categ_id.is_pack_service"
    )

    @api.depends("categ_id")
    def _compute_pack_type(self):
        for record in self:
            record.pack_type = PACK_TYPE_NONE
            if record.categ_id:
                record.pack_type = record.categ_id.pack_type

    @api.depends("property_contract_template_id")
    def _compute_related_contract_product_ids(self):
        for record in self:
            rel_products = [(5, 0, 0)]
            record.related_contract_product_ids = rel_products
            if record.property_contract_template_id:
                for line in record.property_contract_template_id.contract_line_ids:
                    rel_products.append((4, line.product_id.id))
                record.related_contract_product_ids = rel_products

    @api.depends("categ_id")
    def _compute_is_config_share(self):
        for record in self:
            record.is_config_share = False
            if record.categ_id:
                record.is_config_share = record.categ_id.is_config_share

    @api.constrains("property_contract_template_id", "categ_id")
    def _constraint_contract_template_pack_type(self):
        for record in self:
            record._compute_pack_type()
        ctemplates = self.env["contract.template"].search([])
        for ctemplate in ctemplates:
            ctemplate._compute_pack_type()

    @api.constrains("description_sale")
    def _constraint_contract_template_line_name(self):
        for record in self:
            ctemplatelines = self.env["contract.template.line"].search(
                [("product_id", "=", record.product_variant_id.id)]
            )
            for ctemplateline in ctemplatelines:
                ctemplateline.write(
                    {
                        "name": ctemplateline.product_id.get_product_multiline_description_sale()
                    }
                )
