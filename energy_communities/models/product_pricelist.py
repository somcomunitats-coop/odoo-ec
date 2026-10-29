from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    company_id = fields.Many2one(default=lambda self: self.env.company)
    user_current_role = fields.Char(compute="_compute_user_current_role")

    @api.depends_context("allowed_company_ids", "active_company_ids")
    def _compute_user_current_role(self):
        role = self.env.user.get_current_role()
        for record in self:
            record.user_current_role = role or False

    def copy(self, default=None):
        # Duplicate always starts on the context company. Platform admins can
        # clear company_id afterwards; other roles see the field as readonly.
        default = dict(default or {})
        default["company_id"] = self.env.company.id
        return super().copy(default)
