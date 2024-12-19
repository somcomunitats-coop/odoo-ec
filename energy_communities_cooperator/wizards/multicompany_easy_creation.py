from odoo import _, api, fields, models


class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _name = "account.multicompany.easy.creation.wiz"
    _inherit = "account.multicompany.easy.creation.wiz"

    parent_id_id = fields.Integer(store=False, compute="_compute_parent_id_id")
    property_cooperator_account = fields.Many2one(
        comodel_name="account.account",
        string="Cooperator Account",
        help="This account will be"
        " the default one as the"
        " receivable account for the"
        " cooperators",
    )
    capital_share = fields.Monetary(string="Initial capital share", default=100)
    product_share_template = fields.Many2one(
        comodel_name="product.template",
        string="Product Share Template",
    )
    new_product_share_template = fields.Many2one(
        comodel_name="product.template",
        string="New Product Share Template",
        readonly=True,
    )
    create_user = fields.Boolean(string="Create user for cooperator", default=True)

    @api.depends("parent_id")
    def _compute_parent_id_id(self):
        for record in self:
            record.parent_id_id = False
            if record.parent_id:
                record.parent_id_id = record.parent_id.id

    @api.onchange("parent_id")
    def _setup_product_share_template(self):
        for record in self:
            record.product_share_template = False
            if record.parent_id:
                share_product_template = self.env["product.template"].search(
                    [("is_share", "=", True), ("company_id", "=", record.parent_id.id)],
                    limit=1,
                )
                if share_product_template:
                    record.product_share_template = share_product_template.id

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
        taxes_id = self.env.ref(
            "l10n_es.{}_account_tax_template_s_iva_ns".format(self.new_company_id.id)
        )
        self.new_product_share_template = self.sudo().product_share_template.copy(
            {
                "name": self.product_share_template.name,
                "company_id": self.new_company_id.id,
                "list_price": self.capital_share,
                "active": True,
                "taxes_id": taxes_id,
            }
        )

    def thread_action_accept(self):
        super().thread_action_accept()
        if self.property_cooperator_account:
            self.set_cooperative_account()
        self.update_product_category_company_share()
        self.create_capital_share_product_template()
        # TODO: propagate create_user to be added to new_company cooperator config
