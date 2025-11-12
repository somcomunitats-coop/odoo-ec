from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    voluntary_share_id = fields.Many2one(
        comodel_name="product.template",
        domain=[("is_share", "=", True)],
        string="Voluntary share to show on website",
        related="company_id.voluntary_share_id",
        readonly=False,
    )
    cooperator_share_form_header_text = fields.Html(
        string="Cooperator share form header text",
        translate=True,
        related="company_id.cooperator_share_form_header_text",
        readonly=False,
    )
    voluntary_share_form_header_text = fields.Html(
        string="Voluntary share form header text",
        translate=True,
        related="company_id.voluntary_share_form_header_text",
        readonly=False,
    )
    voluntary_share_journal_account = fields.Many2one(
        "account.journal",
        "Voluntary shares journal",
        check_company=True,
        related="company_id.voluntary_share_journal_account",
        readonly=False,
    )
    voluntary_share_email_template = fields.Many2one(
        comodel_name="mail.template",
        string="Voluntary share return email template",
        domain=[("model", "=", "account.move")],
        help="If left empty, the default global mail template will be used.",
        related="company_id.voluntary_share_email_template",
        readonly=False,
    )
