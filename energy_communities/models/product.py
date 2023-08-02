from odoo import api, fields, models
from odoo.http import request

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_web_share_products(self, is_company):
        """We are fully overriding this function in order to make it multi-company sensitive"""
        
        if request:
            default_company = request.env["res.company"]._company_default_get()
        else:
            default_company = self.env.user_id.company_id

        target_company = default_company

        if self.env.context.get('target_odoo_company_id',False) and self.env.context.get('target_odoo_company_id') != default_company.id:
            target_company = self.env['res.company'].browse(self.env.context.get('target_odoo_company_id'))

        if is_company is True:
            product_templates = self.env["product.template"].search(
                [
                    ("is_share", "=", True),
                    ("display_on_website", "=", True),
                    ("by_company", "=", True),
                    ("company_id", "=", target_company.id),
                ]
            )
        else:
            product_templates = self.env["product.template"].search(
                [
                    ("is_share", "=", True),
                    ("display_on_website", "=", True),
                    ("by_individual", "=", True),
                    ("company_id", "=", target_company.id),
                ]
            )
        return product_templates

    @api.model
    def create(self, vals):
        if self.env.user not in (self.env.ref("base.user_root"),
                                self.env.ref("base.user_admin"),
                                self.env.ref("base.default_user"),
                                self.env.ref("base.public_user"),
                                self.env.ref("base.template_portal_user_id")):
            if not vals.get('company_id', False):
                vals['company_id'] = self.env.company.id

        product = super(ProductTemplate, self).create(vals)
        return product