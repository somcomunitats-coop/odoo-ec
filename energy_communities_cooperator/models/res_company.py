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
    voluntary_share_journal_account = fields.Many2one(
        "account.journal",
        "Voluntary shares journal",
        check_company=True,
    )
    voluntary_share_email_template = fields.Many2one(
        comodel_name="mail.template",
        string="Voluntary share return email template",
        domain=[("model", "=", "account.move")],
        help="If left empty, the default global mail template will be used.",
    )

    def action_open_volutary_share_interest_return_wizard(self):
        wizard = self.env["voluntary.share.interest.return.wizard"].create(
            {"company_id": self.id}
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Return voluntary shares interest"),
            "res_model": "voluntary.share.interest.return.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }

    def get_voluntary_share_return_email_template(self):
        if self.voluntary_share_email_template:
            return self.voluntary_share_email_template
        else:
            return self.env.ref(
                "energy_communities_cooperator.email_template_voluntary_share_interest_return"
            )
