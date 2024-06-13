from odoo import fields, models
from odoo.tools.translate import _


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    voluntary_share_id = fields.Many2one(
        comodel_name="product.template",
        domain=[("is_share", "=", True)],
        string="Voluntary share to show on website",
    )
    cooperator_share_form_header_text = fields.Html(
        string="Cooperator share form header text", translate=True
    )
    voluntary_share_form_header_text = fields.Html(
        string="Voluntary share form header text", translate=True
    )

    def action_open_volutary_share_interest_return_wizard(self):
        wizard = self.env["voluntary.share.interest.return.wizard"].create({})
        return {
            "type": "ir.actions.act_window",
            "name": _("Return voluntary shares interest"),
            "res_model": "voluntary.share.interest.return.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }
