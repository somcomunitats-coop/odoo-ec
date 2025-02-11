from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    property_contract_template_id = fields.Many2one(
        company_dependent=False,
    )
    related_contract_product_ids = fields.One2many(
        "product.product",
        string="Related services",
        compute="_compute_related_contract_product_ids",
        store=False,
    )
    pack_type = fields.Selection(related="property_contract_template_id.pack_type")

    @api.depends("property_contract_template_id")
    def _compute_related_contract_product_ids(self):
        for record in self:
            rel_products = [(5, 0, 0)]
            record.related_contract_product_ids = rel_products
            if record.property_contract_template_id:
                for line in record.property_contract_template_id.contract_line_ids:
                    rel_products.append((4, line.product_id.id))
                record.related_contract_product_ids = rel_products

    @api.constrains("property_contract_template_id")
    def _constraint_contract_template_pack_type(self):
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
