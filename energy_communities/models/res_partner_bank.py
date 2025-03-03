from odoo import api, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    _sql_constraints = [
        (
            "unique_number",
            "unique(sanitized_acc_number, company_id, partner_id)",
            "Account Number must be unique",
        ),
    ]

    # https://github.com/OCA/bank-payment/blob/16.0/account_banking_mandate/models/res_partner_bank.py
    # TODO: I+D: Check why setting company_id and company_ids on partner triggers bank account company_id constrain
    # @api.constrains("company_id")
    # def _company_constrains(self):
    #     return True
