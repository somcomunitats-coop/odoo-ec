from odoo import fields, models


class Contract(models.Model):
    _inherit = "contract.contract"

    supply_point_assignation_id = fields.Many2one(
        "energy_selfconsumption.supply_point_assignation",
        string="Selfconsumption project",
    )
    project_id = fields.Many2one(
        "energy_project.project",
        ondelete="restrict",
        string="Energy Project",
        related="supply_point_assignation_id.distribution_table_id.selfconsumption_project_id.project_id",
        store=True,
        auto_join=True,
    )
    code = fields.Char(related="supply_point_assignation_id.supply_point_id.code")
    supply_point_name = fields.Char(
        related="supply_point_assignation_id.supply_point_id.name"
    )
    last_period_date_start = fields.Date(
        string="Last Period Start",
        readonly=True,
    )
    last_period_date_end = fields.Date(
        string="Last Period End",
        readonly=True,
    )

    def invoicing_wizard_action(self):
        """
        We create the wizard first, so it triggers the constraint of the contract_ids
        :return: Window action with the wizard already created
        """
        wizard_id = self.env["energy_selfconsumption.invoicing.wizard"].create(
            {"contract_ids": [(6, 0, self.ids)]}
        )
        action = self.env.ref(
            "energy_selfconsumption.invoicing_wizard_act_window"
        ).read()[0]
        action["res_id"] = wizard_id.id
        return action

    def _recurring_create_invoice(self, date_ref=False):
        last_period_date_start = last_period_date_end = False
        if len(self) > 1:
            last_period_date_start = self[0].next_period_date_start
            last_period_date_end = self[0].next_period_date_end
        res = super()._recurring_create_invoice(date_ref=date_ref)
        if res and last_period_date_start and last_period_date_end:
            self.write(
                {
                    "last_period_date_start": last_period_date_start,
                    "last_period_date_end": last_period_date_end,
                }
            )
        return res

    def _get_contracts_to_invoice_domain(self, date_ref=None):
        domain = super()._get_contracts_to_invoice_domain(date_ref)
        domain.extend(
            [("project_id.selfconsumption_id.invoicing_mode", "!=", "energy_delivered")]
        )
        return domain


class ContractRecurrencyMixin(models.AbstractModel):
    _inherit = "contract.recurrency.mixin"

    next_period_date_start = fields.Date(store=True)
    next_period_date_end = fields.Date(store=True)
