import hashlib

from odoo import fields, models
from odoo.tools.translate import _


class ResCompany(models.Model):
    _name = "res.company"
    _inherit = "res.company"

    def _compute_company_external_id(self):
        for record in self:
            record.company_external_id = hashlib.sha1(
                str(record.id).encode()
            ).hexdigest()

    def _compute_share_urls(self):
        for record in self:
            record.voluntary_share_url_individual = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/become_cooperator?external_company_id={record.company_external_id}"
            record.voluntary_share_url_company = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/become_company_cooperator?external_company_id={record.company_external_id}"
            record.invitation_share_url_individual = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/become_invited?external_company_id={record.company_external_id}"
            record.invitation_share_url_company = f"{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/become_company_invited?external_company_id={record.company_external_id}"

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

    product_website = fields.Boolean(string="Product selector in BASE form")

    company_external_id = fields.Char(
        string="External ID", compute="_compute_company_external_id", store=True
    )

    voluntary_share_url_individual = fields.Char(
        string="Voluntary share URL individual",
        compute="_compute_share_urls",
        readonly=True,
    )
    voluntary_share_url_company = fields.Char(
        string="Voluntary share URL company",
        compute="_compute_share_urls",
        readonly=True,
    )

    invitation_share_url_individual = fields.Char(
        string="Invitation share URL individual",
        compute="_compute_share_urls",
        readonly=True,
    )
    invitation_share_url_company = fields.Char(
        string="Invitation share URL company",
        compute="_compute_share_urls",
        readonly=True,
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

    # TODO: This method has been overwritten from original method on cooperator.
    # Find a better way of doing this using ACL and record rules
    def _init_cooperator_demo_data(self):
        if (
            not self.env["ir.module.module"]
            .sudo()
            .search([("name", "=", "cooperator")])
            .demo
        ):
            # demo data must not be loaded, nothing to do
            return
        account_account_model = self.env["account.account"].sudo()
        for company in self:
            if not company._accounting_data_initialized():
                # same remark as in _init_cooperator_data()
                continue
            if not company.property_cooperator_account:
                company.property_cooperator_account = account_account_model.create(
                    {
                        "code": "416101",
                        "name": "Cooperators",
                        "account_type": "asset_receivable",
                        "reconcile": True,
                        "company_id": company.id,
                    }
                )
