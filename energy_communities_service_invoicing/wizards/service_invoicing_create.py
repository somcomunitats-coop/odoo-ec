from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ServiceInvoicingCreateWizard(models.TransientModel):
    _name = "service.invoicing.create.wizard"
    _description = "Create service invoicing for an energy community"

    company_id = fields.Many2one("res.company", string="Coordinator")
    community_company_id = fields.Many2one("res.company", string="Community")
    service_id = fields.Many2one("product.product", string="Service")

    def execute_create(self):
        return True
        # self._consistency_validation()
        # voluntary_share_interest_return = self.env[
        #     "voluntary.share.interest.return"
        # ].create(
        #     {
        #         "name": "{company_name} voluntary share interest return from {start_date_period} to {end_date_period}".format(
        #             company_name=self.company_id.name,
        #             start_date_period=self.start_date_period,
        #             end_date_period=self.end_date_period,
        #         ),
        #         "start_date_period": self.start_date_period,
        #         "end_date_period": self.end_date_period,
        #         "payment_mode_id": self.payment_mode_id.id,
        #     }
        # )
        # return {
        #     "type": "ir.actions.act_window",
        #     "name": _("Return voluntary shares interest"),
        #     "res_model": "voluntary.share.interest.return",
        #     "view_type": "form",
        #     "view_mode": "form",
        #     "target": "current",
        #     "res_id": voluntary_share_interest_return.id,
        # }
