from odoo import fields, models, api

import logging
_logger = logging.getLogger(__name__)
class AccountMulticompanyEasyCreationWiz(models.TransientModel):
    _inherit = "account.multicompany.easy.creation.wiz"

    crm_lead_id = fields.Many2one('crm.lead', string="CRM Lead")
    property_cooperator_account = fields.Many2one(
        comodel_name="account.account",
        string="Cooperator Account",
        domain=[
            ("internal_type", "=", "receivable"),
            ("deprecated", "=", False),
        ],
        help="This account will be"
             " the default one as the"
             " receivable account for the"
             " cooperators",
    )

    def update_product_category_company_share(self):
        new_company_id = self.new_company_id.id
        self_new_company = self.with_company(new_company_id)
        product_category_company_share = self_new_company.env.ref('cooperator.product_category_company_share')
        account_chart_external_id = list(self.chart_template_id.get_external_id().values())[0]
        _logger.info(account_chart_external_id)
        values = {
            'l10n_es.account_chart_template_common': {
                'property_account_income_categ_id': 'l10n_es.{}_account_common_101'.format(new_company_id),
                'property_account_expense_categ_id': 'l10n_es.{}_account_common_119'.format(new_company_id)
            },
            'l10n_es.account_chart_template_pymes': {
                'property_account_income_categ_id': 'l10n_es.{}_account_pymes_100'.format(new_company_id),
                'property_account_expense_categ_id': 'l10n_es.{}_account_pymes_120'.format(new_company_id)
            },
            'l10n_es.account_chart_template_assoc': {
                'property_account_income_categ_id': 'l10n_es.{}_account_assoc_100'.format(new_company_id),
                'property_account_expense_categ_id': 'l10n_es.{}_account_assoc_120'.format(new_company_id)
            },
            'l10n_es.account_chart_template_full': {
                'property_account_income_categ_id': 'l10n_es.{}_account_full_100'.format(new_company_id),
                'property_account_expense_categ_id': 'l10n_es.{}_account_full_120'.format(new_company_id)
            },
        }.get(account_chart_external_id, False)
        _logger.info("VALUES")
        _logger.info(values)

        if values:
            product_category_company_share.write(values)

    def action_accept(self):
        action = super(AccountMulticompanyEasyCreationWiz, self).action_accept()
        self.update_product_category_company_share()
        return action
