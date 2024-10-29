from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)
        defaults["company_id"] = self.env.company.id
        return defaults
