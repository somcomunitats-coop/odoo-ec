from odoo import api, fields, models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _compute_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for record in self:
            record.url_individual = (
                f"{base_url}/become_cooperator?odoo_company_id={record.company_id.id}"
            )
            record.url_company = f"{base_url}/become_company_cooperator?odoo_company_id={record.company_id.id}"

    mail_template = fields.Many2one(
        comodel_name="mail.template",
        string="Certificate email template",
        domain=[("model", "=", "res.partner")],
        help="If left empty, the default global mail template will be used.",
    )
    url_individual = fields.Char(
        String="URL individual", compute="_compute_url", readonly=True
    )
    url_company = fields.Char(
        String="URL company", compute="_compute_url", readonly=True
    )

    # TODO: This must be interated on new coopeator version
    def get_web_share_products(self, is_company):
        """We are fully overriding this function in order to make it multi-company sensitive"""

        if request:
            default_company = request.env["res.company"].browse(
                request.env.context.get("target_odoo_company_id")
            )
        else:
            default_company = self.env.user_id.company_id

        target_company = default_company

        if (
            self.env.context.get("target_odoo_company_id", False)
            and self.env.context.get("target_odoo_company_id") != default_company.id
        ):
            target_company = self.env["res.company"].browse(
                self.env.context.get("target_odoo_company_id")
            )

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
