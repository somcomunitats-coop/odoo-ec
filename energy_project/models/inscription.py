from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Inscription(models.Model):
    _name = "energy_project.inscription"
    _description = "Inscriptions for a project"

    _sql_constraints = {
        (
            "unique_project_id_partner_id",
            "unique (project_id, partner_id)",
            _("Partner is already signed up in this project."),
        )
    }

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, readonly=True
    )
    project_id = fields.Many2one(
        "energy_project.project",
        required=True,
        ondelete="restrict",
        string="Energy Project",
        check_company=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        string="Partner",
    )
    effective_date = fields.Date(required=True)
    is_member = fields.Char(
        string=_("Typology"), compute="_compute_is_member", readonly=True
    )

    @api.depends("partner_id.member")
    def _compute_is_member(self):
        for record in self:
            record.is_member = (
                _("Partner") if record.partner_id.member else _("Non-partner")
            )

    def has_matching_supply_assignations(self):
        matching_tables = (
            self.project_id.selfconsumption_id.distribution_table_ids.filtered(
                lambda table: table.state in ("validated", "process", "active")
            )
        )
        matching_assignations = matching_tables.mapped(
            "supply_point_assignation_ids"
        ).filtered(
            lambda assignation: assignation.supply_point_id.partner_id
            == self.partner_id
        )
        return matching_assignations

    def get_matching_supply_assignations_to_remove(self):
        supply_point_assignations = self.env[
            "energy_selfconsumption.supply_point_assignation"
        ].search(
            [
                ("supply_point_id.partner_id", "=", self.partner_id.id),
                ("selfconsumption_project_id", "=", self.project_id.id),
                ("distribution_table_id.state", "=", "draft"),
            ]
        )
        return supply_point_assignations

    def unlink(self):
        matching_assignations = self.has_matching_supply_assignations()
        if len(matching_assignations) > 0:
            table_states = ", ".join(
                matching_assignations.distribution_table_id.mapped("state")
            )
            raise ValidationError(
                _(
                    "The inscription cannot be deleted. It is related to a distribution table with state: {table_state}"
                ).format(table_state=table_states)
            )
        supply_point_assignations = self.get_matching_supply_assignations_to_remove()
        if supply_point_assignations:
            supply_point_assignations.unlink()
        return super().unlink()
