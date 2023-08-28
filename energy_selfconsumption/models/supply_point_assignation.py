from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SupplyPointAssignation(models.Model):
    _name = "energy_selfconsumption.supply_point_assignation"
    _description = "Supply Point Assignation"

    @api.depends("distribution_table_id")
    def _compute_supply_point_filtered_ids(self):
        """
        List of supply point of partners subscribed to the project and not in the list of the distribution table to
        prevent multiple assignations of same supply point.
        Used to filter out in the view.
        :return:
        """
        for record in self:
            record.supply_point_filtered_ids = record.distribution_table_id.selfconsumption_project_id.inscription_ids.mapped(
                "partner_id.supply_ids"
            ).filtered_domain(
                [
                    (
                        "id",
                        "not in",
                        record.distribution_table_id.supply_point_assignation_ids.mapped(
                            "supply_point_id.id"
                        ),
                    )
                ]
            )

    distribution_table_id = fields.Many2one(
        "energy_selfconsumption.distribution_table", required=True
    )
    selfconsumption_project_id = fields.Many2one(
        related="distribution_table_id.selfconsumption_project_id"
    )
    distribution_table_state = fields.Selection(related="distribution_table_id.state")
    distribution_table_create_date = fields.Datetime(
        related="distribution_table_id.create_date"
    )
    supply_point_id = fields.Many2one(
        "energy_selfconsumption.supply_point", required=True
    )
    coefficient = fields.Float(
        string="Distribution coefficient",
        digits=(1, 5),
        required=True,
        help="The sum of all the coefficients must result in 1",
    )
    owner_id = fields.Many2one("res.partner", related="supply_point_id.owner_id")
    code = fields.Char(related="supply_point_id.code")
    table_coefficient_is_valid = fields.Boolean(
        related="distribution_table_id.coefficient_is_valid"
    )

    supply_point_filtered_ids = fields.One2many(
        "energy_selfconsumption.supply_point",
        compute=_compute_supply_point_filtered_ids,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, readonly=True
    )

    @api.constrains("coefficient")
    def constraint_coefficient(self):
        for record in self:
            if record.coefficient < 0:
                raise ValidationError(_("Coefficient can't be negative."))

    @api.constrains("supply_point_id")
    def constraint_supply_point_id(self):
        for record in self:
            supply_points = record.distribution_table_id.selfconsumption_project_id.inscription_ids.mapped(
                "partner_id.supply_ids"
            )
            if record.supply_point_id.id not in supply_points.ids:
                raise ValidationError(
                    _(
                        "The partner of the supply point is not subscribed to the project"
                    )
                )

    @api.onchange("coefficient")
    def _onchange_coefficient(self):
        if self.coefficient < 0:
            self.coefficient = -self.coefficient
        if self.coefficient > 1:
            self.coefficient = 1
