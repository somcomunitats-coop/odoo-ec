import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)

TYPE_VALUES = [
    ("fixed", _("Fixed")),
    # ("hourly", _("Variable hourly"))
]

DISTRIBUTE_EXCESS_VALUES = [("yes", _("Yes")), ("no", _("No"))]

TYPE_DISTRIBUTE_EXCESS_VALUES = [
    ("proportional", _("Proportional")),
    ("linear", _("Linear")),
]


class CreateDistributionTableWizard(models.TransientModel):
    _name = "energy_selfconsumption.create_distribution_table.wizard"
    _description = "Service to generate distribution table"

    percentage_of_distributed_power = fields.Float(
        string="Percentage of distributed power", readonly=True
    )

    distributed_power = fields.Float(string="Distributed power", readonly=True)

    max_distributed_power = fields.Float(string="Max distributed power", readonly=True)

    type = fields.Selection(
        TYPE_VALUES, default="fixed", required=True, string="Modality"
    )

    distribute_excess = fields.Selection(
        DISTRIBUTE_EXCESS_VALUES,
        default="no",
        required=True,
        string="Distribute excess",
    )

    type_distribute_excess = fields.Selection(
        TYPE_DISTRIBUTE_EXCESS_VALUES,
        default="proportional",
        required=True,
        string="Type distribute excess",
    )

    @api.model
    def default_get(self, default_fields):
        # OVERRIDE
        default_fields = super().default_get(default_fields)

        if len(self.env.context.get("active_ids", [])) == 0:
            raise ValidationError(_("You have to select at least one entry."))

        inscriptions = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].browse(self.env.context.get("active_ids", []))

        selfconsumption = (
            self.env["energy_selfconsumption.selfconsumption"]
            .sudo()
            .search([("project_id", "=", inscriptions[0].project_id.id)])
        )

        if selfconsumption.power == 0:
            raise ValidationError(_("The project has to have a power greater than 0."))

        default_fields["max_distributed_power"] = selfconsumption.power

        default_fields["distributed_power"] = sum(
            map(lambda inscription: inscription.participation_quantity, inscriptions)
        )

        default_fields["percentage_of_distributed_power"] = (
            default_fields["distributed_power"]
            / default_fields["max_distributed_power"]
        ) * 100

        if default_fields["percentage_of_distributed_power"] == 0:
            raise ValidationError(_("Your distribution percentage cannot be 0."))

        if default_fields["percentage_of_distributed_power"] > 100:
            raise ValidationError(_("Your distribution percentage cannot exceed 100%."))

        return default_fields

    def create_distribution_table(self):
        inscriptions = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].browse(self.env.context.get("active_ids", []))

        selfconsumption = (
            self.env["energy_selfconsumption.selfconsumption"]
            .sudo()
            .search([("project_id", "=", inscriptions[0].project_id.id)])
        )

        distribution_table = self.env[
            "energy_selfconsumption.distribution_table"
        ].create(
            {
                "selfconsumption_project_id": selfconsumption.id,
                "type": self.type,
            }
        )

        values_list = []
        for inscription in inscriptions:
            values_list.append(
                self.get_supply_point_assignation_values(
                    inscription, distribution_table, len(inscriptions)
                )
            )

        self.env[
            "energy_selfconsumption.create_distribution_table"
        ].create_energy_selfconsumption_supply_point_assignation_sql(
            values_list, distribution_table
        )

        return selfconsumption.get_distribution_tables()

    def get_supply_point_assignation_values(
        self, inscription, distribution_table, len_inscriptions
    ):
        coefficient = inscription.participation_quantity

        if self.distribute_excess == "yes":
            distribute_excess_float = (
                self.max_distributed_power - self.distributed_power
            )

            if self.type_distribute_excess == "proportional":
                coefficient += distribute_excess_float * (
                    inscription.participation_quantity / self.distributed_power
                )
            else:
                coefficient += distribute_excess_float / len_inscriptions

        coefficient = coefficient / self.max_distributed_power

        return {
            "distribution_table_id": distribution_table.id,
            "supply_point_id": inscription.supply_point_id.id,
            "coefficient": coefficient,
            "company_id": distribution_table.company_id.id,
        }
