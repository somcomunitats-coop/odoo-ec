import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _inherit = "account.multicompany.easy.creation.wiz"

    def _default_product_share_template(self):
        return self.env.ref(
            "energy_communities.share_capital_product_template",
            raise_if_not_found=False,
        )

    parent_id = fields.Many2one(
        "res.company",
        string="Parent Coordinator Company",
        index=True,
        required=True,
        domain=[("hierarchy_level", "=", "coordinator")],
    )
    crm_lead_id = fields.Many2one("crm.lead", string="CRM Lead")
    property_cooperator_account = fields.Many2one(
        comodel_name="account.account",
        string="Cooperator Account",
        help="This account will be"
        " the default one as the"
        " receivable account for the"
        " cooperators",
    )
    capital_share = fields.Monetary(string="Initial capital share", default=100)
    create_user = fields.Boolean(string="Create user for cooperator", default=True)
    chart_template_id = fields.Many2one(
        comodel_name="account.chart.template",
        string="Chart Template",
        domain=[("visible", "=", True)],
    )
    product_share_template = fields.Many2one(
        comodel_name="product.template",
        default=_default_product_share_template,
        string="Product Share Template",
        domain=[("is_share", "=", True)],
    )
    new_product_share_template = fields.Many2one(
        comodel_name="product.template",
        string="New Product Share Template",
        readonly=True,
    )

    default_lang_id = fields.Many2one(
        comodel_name="res.lang",
        string="Language",
    )

    street = fields.Char(
        string="Address",
    )

    city = fields.Char(
        string="City",
    )

    zip_code = fields.Char(
        string="ZIP code",
    )

    foundation_date = fields.Date(string="Foundation date")

    vat = fields.Char(
        string="ZIP code",
    )

    email = fields.Char(
        string="Email",
    )

    phone = fields.Char(
        string="Phone",
    )

    website = fields.Char(
        string="Website",
    )

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="State",
    )

    def add_company_managers(self):
        coord_members = self.parent_id.get_users(
            ["role_coord_admin", "role_coord_worker"]
        )
        for manager in coord_members:
            manager.make_ce_user(self.new_company_id, "role_ce_manager")

    def add_company_log(self):
        message = _(
            "Community created from: <a href='/web#id={id}&view_type=form&model=crm.lead&menu_id={menu_id}'>{name}</a>"
        )
        self_new_company = self.with_company(self.new_company_id)
        self_new_company.new_company_id.message_post(
            body=message.format(
                id=self.crm_lead_id.id,
                menu_id=self.env.ref("crm.crm_menu_root").id,
                name=self.crm_lead_id.name,
            )
        )

    def update_product_category_company_share(self):
        new_company_id = self.new_company_id.id
        self_new_company = self.with_company(new_company_id)
        product_category_company_share = self_new_company.env.ref(
            "cooperator.product_category_company_share"
        )
        account_chart_external_id = list(
            self.chart_template_id.get_external_id().values()
        )[0]
        values = {
            "l10n_es.account_chart_template_pymes": {
                "property_account_income_categ_id": "l10n_es.{}_account_pymes_100".format(
                    new_company_id
                ),
                "property_account_expense_categ_id": "l10n_es.{}_account_pymes_100".format(
                    new_company_id
                ),
            },
            "l10n_es.account_chart_template_assoc": {
                "property_account_income_categ_id": "l10n_es.{}_account_assoc_100".format(
                    new_company_id
                ),
                "property_account_expense_categ_id": "l10n_es.{}_account_assoc_100".format(
                    new_company_id
                ),
            },
            "l10n_es.account_chart_template_full": {
                "property_account_income_categ_id": "l10n_es.{}_account_full_100".format(
                    new_company_id
                ),
                "property_account_expense_categ_id": "l10n_es.{}_account_full_100".format(
                    new_company_id
                ),
            },
        }.get(account_chart_external_id, False)

        values["property_account_income_categ_id"] = self.env.ref(
            values["property_account_income_categ_id"]
        )
        values["property_account_expense_categ_id"] = self.env.ref(
            values["property_account_expense_categ_id"]
        )
        product_category_company_share.write(values)

    def create_capital_share_product_template(self):
        new_company_id = self.new_company_id.id
        self_new_company = self.with_company(new_company_id)
        # We use sudo to be able to copy the product and not needing to be in the main company
        self.new_product_share_template = self.sudo().product_share_template.copy(
            {
                "name": self.product_share_template.name,
                "company_id": self.new_company_id.id,
                "list_price": self.capital_share,
                "active": True,
            }
        )
        self_new_company.new_company_id.initial_subscription_share_amount = (
            self.capital_share
        )

    def update_values_from_crm_lead(self):
        if self.crm_lead_id:
            vals = self.crm_lead_id._get_default_community_wizard()
            self.new_company_id.write(vals)

    def set_cooperative_account(self):
        self_new_company = self.with_company(self.new_company_id)
        new_company = self_new_company.new_company_id
        new_company.write(
            {
                "property_cooperator_account": self.match_account(
                    self.property_cooperator_account
                ).id
            }
        )

    def set_cooperator_journal(self):
        """
        This method is only used in the creation from data. Is used to assign the subcription journal in the res.company
        configuration.
        This need to execute after the creation of the company because searching is the only way to reference the journal
        created in the aplication of the account.chart.template see acoount_chart_template.py#L10
        :return:
        """
        self.new_company_id.cooperator_journal = (
            self.env["account.journal"].search(
                [("code", "=", "SUBJ"), ("company_id", "=", self.new_company_id.id)]
            )
            or False
        )

    def action_accept(self):
        action = super().action_accept()
        # self.update_values_from_crm_lead()
        if self.property_cooperator_account:
            self.set_cooperative_account()
        self_new_company = self.with_company(self.new_company_id)
        self_new_company.new_company_id.create_user = self.create_user
        self.update_product_category_company_share()
        self.create_capital_share_product_template()
        self.add_company_managers()
        self.add_company_log()
        return action

    def create_company(self):
        self.new_company_id = (
            self.env["res.company"]
            .sudo()
            .create(
                {
                    "name": self.name,
                    "user_ids": [(6, 0, self.user_ids.ids)],
                    "parent_id": self.parent_id.id,
                }
            )
        )
        allowed_company_ids = (
            self.env.context.get("allowed_company_ids", []) + self.new_company_id.ids
        )
        new_company = self.new_company_id.with_context(
            allowed_company_ids=allowed_company_ids
        )
        self.with_context(
            allowed_company_ids=allowed_company_ids
        ).sudo().chart_template_id.try_loading(company=new_company)
        self.create_bank_journals()
        self.create_sequences()
