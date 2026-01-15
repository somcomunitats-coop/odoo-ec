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

    numberof_effective_inviteds = fields.Integer(
        string="Number of effective inviteds",
        compute="_compute_numberof_effective_inviteds",
        store=False,
    )
    numberof_effective_members = fields.Integer(
        string="Number of effective cooperators",
        compute="_compute_numberof_effective_members",
        store=False,
    )
    numberof_effective_cooperators = fields.Integer(
        string="Number of effective cooperators",
        compute="_compute_numberof_effective_cooperators",
        store=False,
    )

    def _compute_numberof_effective_inviteds(self):
        for record in self:
            numberof_effective_inviteds = 0
            effective_inviteds = (
                self.env["res.partner"]
                .with_company(record)
                .search([("no_member_autorized_in_energy_actions", "=", True)])
            )
            # We check the invited is not considered effective cooperator to increase the value
            for effective_invited in effective_inviteds:
                if (
                    not self.env["cooperative.membership"]
                    .with_company(record)
                    .search(
                        [
                            ("partner_id", "=", effective_invited.id),
                            ("company_id", "=", record.id),
                            ("member", "=", True),
                        ]
                    )
                ):
                    # if non_cooperator.with_company(record).no_member_autorized_in_energy_actions:
                    numberof_effective_inviteds += 1
            record.numberof_effective_inviteds = numberof_effective_inviteds

    def _compute_numberof_effective_members(self):
        for record in self:
            record.numberof_effective_members = (
                self.env["cooperative.membership"]
                .with_company(record)
                .search_count([("company_id", "=", record.id), ("member", "=", True)])
            )

    def _compute_numberof_effective_cooperators(self):
        for record in self:
            record.numberof_effective_cooperators = (
                record.numberof_effective_members + record.numberof_effective_inviteds
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
