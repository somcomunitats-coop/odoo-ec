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
    mandate_id = fields.Many2one(
        "account.banking.mandate", string="Bank Mandate", required=True
    )
    acc_number = fields.Char(related="mandate_id.partner_bank_id.acc_number")
    mandate_filtered_ids = fields.One2many(
        "account.banking.mandate", compute="_compute_mandate_filtered_ids"
    )

    @api.depends("partner_id")
    def _compute_mandate_filtered_ids(self):
        for record in self:
            mandates = self.env["account.banking.mandate"].search(
                [
                    ("partner_id", "=", record.partner_id.id),
                    ("company_id", "=", record.company_id.id),
                    ("state", "=", "valid"),
                ]
            )
            record.mandate_filtered_ids = mandates or False

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

    @api.constrains("mandate_id", "partner_id")
    def _check_mandate_id_belongs_to_partner(self):
        for record in self:
            if record.mandate_id and record.partner_id:
                if record.mandate_id.partner_id != record.partner_id:
                    raise ValidationError(
                        _("The selected mandate does not belong to the chosen partner.")
                    )
