from odoo import api, fields, models


class AccountBankingMandate(models.Model):
    _inherit = "account.banking.mandate"

    # _sql_constraints = [
    #     (
    #         "mandate_ref_company_uniq",
    #         "unique(unique_mandate_reference,company_id)",
    #         "A Mandate with the same reference already exists for this company!",
    #     )
    # ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (vals.get("unique_mandate_reference") or "/") == "/":
                vals["unique_mandate_reference"] = (
                    self.env["ir.sequence"].next_by_code("account.banking.mandate")
                    or "New"
                )
        __import__("ipdb").set_trace()
        return super().create(vals_list)
