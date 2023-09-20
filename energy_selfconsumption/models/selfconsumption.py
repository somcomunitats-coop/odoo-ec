from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class Selfconsumption(models.Model):
    _name = "energy_selfconsumption.selfconsumption"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {
        "energy_project.project": "project_id",
    }
    _description = "Self-consumption Energy Project"

    def _compute_distribution_table_count(self):
        for record in self:
            record.distribution_table_count = len(record.distribution_table_ids)

    def _compute_inscription_count(self):
        for record in self:
            record.inscription_count = len(record.inscription_ids)

    def _compute_report_distribution_table(self):
        """
        This compute field gets the distribution table needed to generate the reports.
        It prioritizes the table in process and then the active one. It can only be one of each.
        """
        for record in self:
            table_in_process = record.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            )
            table_in_active = record.distribution_table_ids.filtered_domain(
                [("state", "=", "active")]
            )
            if table_in_process:
                record.report_distribution_table = table_in_process
            elif table_in_active:
                record.report_distribution_table = table_in_active
            else:
                record.report_distribution_table = False

    project_id = fields.Many2one(
        "energy_project.project", required=True, ondelete="cascade"
    )
    code = fields.Char(string="CAU")
    cil = fields.Char(
        string="CIL", help="Production facility code for liquidation purposes"
    )
    owner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
        default=lambda self: self.env.company.partner_id,
    )
    power = fields.Float(string="Generation Power (kW)")
    distribution_table_ids = fields.One2many(
        "energy_selfconsumption.distribution_table",
        "selfconsumption_project_id",
        readonly=True,
    )
    report_distribution_table = fields.Many2one(
        "energy_selfconsumption.distribution_table",
        compute=_compute_report_distribution_table,
        readonly=True,
    )
    distribution_table_count = fields.Integer(compute=_compute_distribution_table_count)
    inscription_ids = fields.One2many(
        "energy_project.inscription", "project_id", readonly=True
    )
    inscription_count = fields.Integer(compute=_compute_inscription_count)

    def get_distribution_tables(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Distribution Tables",
            "view_mode": "tree,form",
            "res_model": "energy_selfconsumption.distribution_table",
            "domain": [("selfconsumption_project_id", "=", self.id)],
            "context": {"create": True, "default_selfconsumption_project_id": self.id},
        }

    def get_inscriptions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Inscriptions",
            "view_mode": "tree,form",
            "res_model": "energy_project.inscription",
            "domain": [("project_id", "=", self.id)],
            "context": {"create": True, "default_project_id": self.id},
        }

    def distribution_table_state(self, actual_state, new_state):
        distribution_table_to_activate = self.distribution_table_ids.filtered(
            lambda table: table.state == actual_state
        )
        distribution_table_to_activate.write({"state": new_state})

    def set_in_activation_state(self):
        for record in self:
            if not record.distribution_table_ids.filtered_domain(
                [("state", "=", "validated")]
            ):
                raise ValidationError(_("Must have a valid Distribution Table."))
            record.write({"state": "activation"})
        self.distribution_table_state("validated", "process")

    def activate(self):
        for record in self:
            if not record.code:
                raise ValidationError(_("Project must have a valid Code."))
            if not record.cil:
                raise ValidationError(_("Project must have a valid CIL."))
            if not record.power or record.power <= 0:
                raise ValidationError(_("Project must have a valid Generation Power."))
            record.write({"state": "active"})
            self.distribution_table_state("process", "active")

    def action_selfconsumption_import_wizard(self):
        self.ensure_one()
        return {
            "name": _("Import Inscriptions and Supply Points"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "energy_selfconsumption.selfconsumption_import.wizard",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
        }

    def set_inscription(self, selfconsumption_state):
        for record in self:
            record.write({"state": "inscription"})
        if selfconsumption_state == "activation":
            self.distribution_table_state("process", "validated")

    def set_draft(self):
        for record in self:
            record.write({"state": "draft"})

    def action_manager_authorization_report(self):
        self.ensure_one()
        return self.env.ref(
            "energy_selfconsumption.selfconsumption_manager_authorization_report"
        ).report_action(self)

    def action_power_sharing_agreement_report(self):
        self.ensure_one()
        return self.env.ref(
            "energy_selfconsumption.power_sharing_agreement_report"
        ).report_action(self)

    def action_manager_partition_coefficient_report(self):
        tables_to_use = self.report_distribution_table
        report_data = []

        for table in tables_to_use:
            for assignation in table.supply_point_assignation_ids:
                report_data.append(
                    {
                        "code": assignation.supply_point_id.code,
                        "coefficient": assignation.coefficient,
                    }
                )

        file_content = ""
        for data in report_data:
            line = f"{data['code']};{str(data['coefficient']).replace('.', ',')}\n"
            file_content += line

        date = datetime.now()
        year = date.strftime("%Y")
        self.env["energy_selfconsumption.coefficient_report"].create(
            {"report_data": file_content, "file_name": f"{self.code}_{year}.txt"}
        )
        url = "/energy_selfconsumption/download_report?id=%s" % self.id
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }


class CoefficientReport(models.TransientModel):
    _name = "energy_selfconsumption.coefficient_report"
    _description = "Generate Partition Coefficient Report"

    report_data = fields.Text("Report Data", readonly=True)
    file_name = fields.Char("File Name", readonly=True)
