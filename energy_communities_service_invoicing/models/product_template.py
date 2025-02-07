from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    property_contract_template_id = fields.Many2one(
        company_dependent=False,
    )

    @api.constrains("property_contract_template_id")
    def compute_contract_template_is_pack(self):
        for record in self:
            ctemplates = self.env["contract.template"].search([])
            for ctemplate in ctemplates:
                ctemplate.compute_is_pack()
