import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

STATE_VALUES = [
    ("active", _("Active")),
    ("inactive", _("Inactive")),
    ("change", _("Change")),
    ("cancelled", _("Cancelled")),
]

STATE_WIZARD_VALUES = [
    ("old", _("Old")),
    ("new", _("New")),
    ("delete", _("Delete")),
    ("change", _("Change")),
]


class Change_distribution_table_import_wizard(models.TransientModel):
    _name = "change.distribution.table.import.wizard"
    _description = _("Change_distribution_table_import_wizard")

    change_distribution_table_import_line_wizard_ids = fields.One2many(
        "change.distribution.table.import.line.wizard",
        "change_distribution_table_import_wizard_id",
        string="Change distribution table import line wizard",
    )

    change_distribution_table_import_line_wizard_news_ids = fields.One2many(
        "change.distribution.table.import.line.wizard",
        "change_distribution_table_import_wizard_id",
        string="Change distribution table import line wizard",
        domain=[("state", "in", ["inactive", "cancelled"])],
    )

    change_distribution_table_import_line_wizard_views_ids = fields.One2many(
        "change.distribution.table.import.line.wizard",
        string="Change distribution table import line wizard",
        compute="_compute_change_distribution_table_import_line_wizard_ids",
    )

    state = fields.Selection(
        STATE_WIZARD_VALUES, required=True, string="Status", default="old"
    )

    @api.model
    def default_get(self, default_fields):
        # OVERRIDE
        default_fields = super().default_get(default_fields)

        inscription_ids = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].search(
            [
                (
                    "selfconsumption_project_id",
                    "=",
                    self.env.context["default_selfconsumption_project_id"],
                ),
                ("state", "=", "active"),
            ]
        )

        lines = []
        for inscription in inscription_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        "change_distribution_table_import_wizard_id": self.id,
                        "inscription_id": inscription.id,
                        "state": inscription.state,
                        "participation_real_quantity": inscription.participation_real_quantity,
                    },
                )
            )

        inscription_ids = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].search(
            [
                (
                    "selfconsumption_project_id",
                    "=",
                    self.env.context["default_selfconsumption_project_id"],
                ),
                ("state", "=", "change"),
            ]
        )
        for inscription in inscription_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        "change_distribution_table_import_wizard_id": self.id,
                        "inscription_id": inscription.id,
                        "state": inscription.state,
                        "participation_real_quantity": inscription.participation_assigned_quantity,
                    },
                )
            )

        default_fields["change_distribution_table_import_line_wizard_ids"] = lines

        inscription_ids = self.env[
            "energy_selfconsumption.inscription_selfconsumption"
        ].search(
            [
                (
                    "selfconsumption_project_id",
                    "=",
                    self.env.context["default_selfconsumption_project_id"],
                ),
                ("state", "in", ["inactive", "cancelled"]),
            ]
        )

        lines = []
        for inscription in inscription_ids:
            lines.append(
                (
                    0,
                    0,
                    {
                        "change_distribution_table_import_wizard_id": self.id,
                        "inscription_id": inscription.id,
                        "state": inscription.state,
                        "participation_real_quantity": inscription.participation_assigned_quantity,
                    },
                )
            )
        default_fields["change_distribution_table_import_line_wizard_news_ids"] = lines
        return default_fields

    @api.depends("state", "change_distribution_table_import_line_wizard_ids")
    def _compute_change_distribution_table_import_line_wizard_ids(self):
        _logger.info(f"self.state: {self.state}")
        if self.state == "old":
            self.change_distribution_table_import_line_wizard_views_ids = (
                self.change_distribution_table_import_line_wizard_ids.filtered(
                    lambda line: line.state == "active"
                )
            )
        elif self.state == "delete":
            self.change_distribution_table_import_line_wizard_views_ids = (
                self.change_distribution_table_import_line_wizard_ids.filtered(
                    lambda line: line.state == "change"
                    and line.participation_real_quantity == 0
                )
            )
        elif self.state == "change":
            self.change_distribution_table_import_line_wizard_views_ids = (
                self.change_distribution_table_import_line_wizard_ids.filtered(
                    lambda line: line.state == "change"
                    and line.participation_real_quantity > 0
                )
            )
        elif self.state == "new":
            self.change_distribution_table_import_line_wizard_views_ids = (
                self.change_distribution_table_import_line_wizard_ids.filtered(
                    lambda line: line.state in ["inactive", "cancelled"]
                )
            )
        else:
            self.change_distribution_table_import_line_wizard_views_ids = (
                self.change_distribution_table_import_line_wizard_ids
            )

    def next_step(self):
        if self.state == "old":
            self.state = "delete"
            return self.action_change_distribution_table_import()
        elif self.state == "delete":
            self.state = "change"
            return self.action_change_distribution_table_import()
        elif self.state == "change":
            self.state = "new"
            return self.action_change_distribution_table_import()
        elif self.state == "new":
            return self.action_create_distribution_table_import()
        else:
            return self.action_change_distribution_table_import()

    def previous_step(self):
        if self.state == "new":
            self.state = "change"
            return self.action_change_distribution_table_import()
        elif self.state == "change":
            self.state = "delete"
            return self.action_change_distribution_table_import()
        elif self.state == "delete":
            self.state = "old"
            return self.action_change_distribution_table_import()
        else:
            return self.action_change_distribution_table_import()

    def action_change_distribution_table_import(self):
        action = self.env.ref(
            "energy_selfconsumption.action_change_distribution_table_import_wizard"
        ).read()[0]
        action.update({"res_id": self.id})
        return action

    def action_create_distribution_table_import(self):
        action = self.env.ref(
            "energy_selfconsumption.create_distribution_table_wizard_action"
        ).read()[0]
        inscription_ids = (
            self.change_distribution_table_import_line_wizard_ids.filtered(
                lambda line: not (
                    line.state == "change" and line.participation_real_quantity == 0
                )
            )
        )
        action.update({"context": {"active_ids": inscription_ids.inscription_id.ids}})
        return action


class Change_distribution_table_import_line_wizard(models.TransientModel):
    _name = "change.distribution.table.import.line.wizard"
    _description = _("Change_distribution_table_import_line_wizard")

    change_distribution_table_import_wizard_id = fields.Many2one(
        "change.distribution.table.import.wizard",
        string="Change state inscription wizard",
        required=True,
    )

    inscription_id = fields.Many2one(
        "energy_selfconsumption.inscription_selfconsumption",
        string="Inscription",
        required=True,
    )

    state = fields.Selection(STATE_VALUES, required=True, string="Status")

    participation_real_quantity = fields.Float(
        string="Participation real quantity", required=True
    )
