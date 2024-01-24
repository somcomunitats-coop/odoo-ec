from odoo import models


class AccountBankingMandate(models.Model):
    _inherit = "account.banking.mandate"

    _sql_constraints = [
        (
            "mandate_ref_company_uniq",
            "unique(company_id, partner_id)",
            "A Mandate with the same partner already exists for this company!",
        )
    ]
