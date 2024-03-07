from datetime import datetime, timedelta

from stdnum.es import cups, referenciacatastral
from stdnum.exceptions import *

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

INVOICING_VALUES = [
    ("power_acquired", _("Power Acquired")),
    ("energy_delivered", _("Energy Delivered")),
    (
        "energy_delivered_variable",
        _("Energy Delivered Variable Hourly Coefficient"),
    ),
]


class Selfconsumption(models.Model):
    _name = "energy_selfconsumption.selfconsumption"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {
        "energy_project.project": "project_id",
    }
    _description = "Self-consumption Energy Project"

    _sql_constraints = [
        (
            "unique_code",
            "UNIQUE(code)",
            _("A project with this CAU already exists."),
        ),
    ]

    def _compute_distribution_table_count(self):
        for record in self:
            record.distribution_table_count = len(record.distribution_table_ids)

    def _compute_inscription_count(self):
        for record in self:
            record.inscription_count = len(record.inscription_ids)

    def _compute_contract_count(self):
        for record in self:
            related_contracts = self.env["contract.contract"].search_count(
                [("project_id", "=", record.id)]
            )
            record.contracts_count = related_contracts

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
    power = fields.Float(string="Rated Power (kWn)")
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
    contracts_count = fields.Integer(compute=_compute_contract_count)
    invoicing_mode = fields.Selection(INVOICING_VALUES, string="Invoicing Mode")
    product_id = fields.Many2one("product.product", string="Product")
    contract_template_id = fields.Many2one(
        "contract.template",
        string="Contract Template",
        related="product_id.contract_template_id",
    )
    supplier_id = fields.Many2one(
        "energy_project.supplier",
        string="Energy Supplier",
        help="Select the associated Energy Supplier",
    )
    cadastral_reference = fields.Char(string="Cadastral reference")

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

    def get_contracts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Contracts",
            "views": [
                [self.env.ref("energy_selfconsumption.contract_tree_view").id, "tree"],
                [False, "form"],
            ],
            "res_model": "contract.contract",
            "domain": [("project_id", "=", self.id)],
            "context": {
                "create": True,
                "default_project_id": self.id,
                "search_default_filter_next_period_date_start": True,
                "search_default_filter_next_period_date_end": True,
            },
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
        """
        Activates the energy self-consumption project, performing various validations.

        This method checks for the presence of a valid code, and rated power
        for the project. If all validations pass, it instances a wizard and generating
        contracts for the project.

        Note:
            The change of state for the 'self-consumption' and 'distribution_table'
            models is performed in the wizard that gets opened. These state changes
            are executed only after the contracts have been successfully generated.

        Returns:
            dict: A dictionary containing the action details for opening the wizard.

        Raises:
            ValidationError: If the project does not have a valid Code, or Rated Power.
        """
        for record in self:
            if not record.code:
                raise ValidationError(_("Project must have a valid Code."))
            if not record.power or record.power <= 0:
                raise ValidationError(_("Project must have a valid Rated Power."))
            if not record.invoicing_mode:
                raise ValidationError(
                    _("Project must have defined a invoicing mode before activation.")
                )
            return {
                "name": _("Generate Contracts"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "energy_selfconsumption.contract_generation.wizard",
                "views": [(False, "form")],
                "view_id": False,
                "target": "new",
                "context": {
                    "default_selfconsumption_id": self.id,
                    "default_company_id": self.env.company.id,
                },
            }

    def set_invoicing_mode(self):
        return {
            "name": _("Define Invoicing Mode"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "energy_selfconsumption.define_invoicing_mode.wizard",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": {"default_selfconsumption_id": self.id},
        }

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

    def validate_state(self, state):
        if state not in ("activation", "active"):
            error_message = _(
                "The report can be downloaded when the project is in activation or active status."
            )
            raise ValidationError(error_message)

    def action_manager_authorization_report(self):
        self.ensure_one()
        self.validate_state(self.state)
        return self.env.ref(
            "energy_selfconsumption.selfconsumption_manager_authorization_report"
        ).report_action(self)

    def action_power_sharing_agreement_report(self):
        self.ensure_one()
        self.validate_state(self.state)
        return self.env.ref(
            "energy_selfconsumption.power_sharing_agreement_report"
        ).report_action(self)

    def action_manager_partition_coefficient_report(self):
        self.validate_state(self.state)
        tables_to_use = self.report_distribution_table
        report_data = []

        for table in tables_to_use:
            for assignation in table.supply_point_assignation_ids:
                coefficient_format = f"{assignation.coefficient:.6f}"  # we need to make sure it has 7 digits
                report_data.append(
                    {
                        "code": assignation.supply_point_id.code,
                        "coefficient": coefficient_format,
                    }
                )

        file_content = ""
        for i, data in enumerate(report_data):
            line = f"{data['code']};{data['coefficient'].replace('.', ',')}"
            if i < len(report_data) - 1:
                line += "\r\n"
            file_content += line

        file_content = file_content.encode("utf-8")

        date = datetime.now()
        year = date.strftime("%Y")
        report = self.env["energy_selfconsumption.coefficient_report"].create(
            {"report_data": file_content, "file_name": f"{self.code}_{year}.txt"}
        )
        url = "/energy_selfconsumption/download_report?id=%s" % report.id
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }

    def send_energy_delivery_invoicing_reminder(self):
        today = fields.date.today()
        date_validation = today + timedelta(days=3)

        projects = self.env["contract.contract"].read_group(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "=",
                    "energy_delivered",
                ),
                ("recurring_next_date", "=", date_validation),
            ],
            ["project_id"],
            ["project_id"],
        )
        template = self.env.ref(
            "energy_selfconsumption.selfconsumption_energy_delivered_invoicing_reminder",
            True,
        )
        for project in projects:
            selfconsumption_id = self.browse(project["project_id"][0])
            contract = selfconsumption_id.contract_ids[0]
            first_date = contract.next_period_date_start
            last_date = contract.next_period_date_end
            next_invoicing = contract.recurring_next_date
            ctx = {
                "next_invoicing": next_invoicing.strftime("%d-%m-%Y"),
                "first_date": first_date.strftime("%d-%m-%Y"),
                "last_date": last_date.strftime("%d-%m-%Y"),
            }
            selfconsumption_id.with_context(ctx).message_post_with_template(template.id)

        return True

    def send_power_acquired_invoicing_reminder(self):
        today = fields.date.today()
        projects = self.env["contract.contract"].read_group(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "=",
                    "power_acquired",
                ),
                ("recurring_next_date", "=", today),
            ],
            ["project_id"],
            ["project_id"],
        )
        template = self.env.ref(
            "energy_selfconsumption.selfconsumption_power_acquired_invoicing_reminder",
            True,
        )
        for project in projects:
            selfconsumption_id = self.browse(project["project_id"][0])
            contract = selfconsumption_id.contract_ids[0]
            next_invoicing = contract.recurring_next_date
            ctx = {
                "next_invoicing": next_invoicing.strftime("%d-%m-%Y"),
            }
            selfconsumption_id.with_context(ctx).message_post_with_template(template.id)

        return True

    @api.constrains("code")
    def _check_valid_code(self):
        """
        The following are evaluated:
            1. The first 20 or 22 digits correspond to the CUPS.
            2. The character after CUPS is A
            3. And the last 3 characters are numbers.
            4. Taking into account that the length of the CUPS can vary, the length of the CAU can be 24 or 26 characters.
        """
        for record in self:
            if record.code:
                # Validate the total length of the CAU, check if the first digits are CUPS and get the last 4 characters
                if len(record.code) == 24:
                    try:
                        cups.validate(record.code[:20])
                    except InvalidLength:
                        error_message = _(
                            "Invalid CAU: The first characters related to CUPS are incorrect. The length is incorrect."
                        )
                        raise ValidationError(error_message)
                    except InvalidComponent:
                        error_message = _(
                            "Invalid CAU: The CUPS does not start with 'ES'."
                        )
                        raise ValidationError(error_message)
                    except InvalidFormat:
                        error_message = _(
                            "Invalid CAU: The CUPS has an incorrect format."
                        )
                        raise ValidationError(error_message)
                    except InvalidChecksum:
                        error_message = _(
                            "Invalid CAU: The checksum of the CUPS is incorrect."
                        )
                        raise ValidationError(error_message)
                    last_digits = record.code[20:]
                elif len(record.code) == 26:
                    try:
                        cups.validate(record.code[:22])
                    except InvalidLength:
                        error_message = _(
                            "Invalid CAU: The first characters related to CUPS are incorrect. The length is incorrect."
                        )
                        raise ValidationError(error_message)
                    except InvalidComponent:
                        error_message = _(
                            "Invalid CAU: The CUPS does not start with 'ES'."
                        )
                        raise ValidationError(error_message)
                    except InvalidFormat:
                        error_message = _(
                            "Invalid CAU: The CUPS has an incorrect format."
                        )
                        raise ValidationError(error_message)
                    except InvalidChecksum:
                        error_message = _(
                            "Invalid CAU: The checksum of the CUPS is incorrect."
                        )
                        raise ValidationError(error_message)
                    last_digits = record.code[22:]
                else:
                    error_message = _("Invalid CAU: The length is not correct")
                    raise ValidationError(error_message)

                # Check if the character after CUPS is 'A'
                if not last_digits.startswith("A"):
                    error_message = _("Invalid CAU: The character after CUPS is not A")
                    raise ValidationError(error_message)

                # Check if the last 3 characters are numbers
                if not last_digits[-3:].isdigit():
                    error_message = _("Invalid CAU: Last 3 digits are not numbers")
                    raise ValidationError(error_message)

    @api.constrains("cil")
    def _check_valid_cil(self):
        """
        The following are evaluated:
            1. The first 20 or 22 digits correspond to the CUPS.
            2. And the last 3 characters are numbers.
        """
        for record in self:
            if record.cil:
                if len(record.cil) == 23:
                    try:
                        cups.validate(record.code[:20])
                    except InvalidLength:
                        error_message = _(
                            "Invalid CIL: The first characters related to CUPS are incorrect. The length is incorrect."
                        )
                        raise ValidationError(error_message)
                    except InvalidComponent:
                        error_message = _(
                            "Invalid CIL: The CUPS does not start with 'ES'."
                        )
                        raise ValidationError(error_message)
                    except InvalidFormat:
                        error_message = _(
                            "Invalid CIL: The CUPS has an incorrect format."
                        )
                        raise ValidationError(error_message)
                    except InvalidChecksum:
                        error_message = _(
                            "Invalid CIL: The checksum of the CUPS is incorrect."
                        )
                        raise ValidationError(error_message)
                    last_digits = record.cil[20:]
                elif len(record.cil) == 25:
                    try:
                        cups.validate(record.code[:22])
                    except InvalidLength:
                        error_message = _(
                            "Invalid CIL: The first characters related to CUPS are incorrect. The length is incorrect."
                        )
                        raise ValidationError(error_message)
                    except InvalidComponent:
                        error_message = _(
                            "Invalid CIL: The CUPS does not start with 'ES'."
                        )
                        raise ValidationError(error_message)
                    except InvalidFormat:
                        error_message = _(
                            "Invalid CIL: The CUPS has an incorrect format."
                        )
                        raise ValidationError(error_message)
                    except InvalidChecksum:
                        error_message = _(
                            "Invalid CIL: The checksum of the CUPS is incorrect."
                        )
                        raise ValidationError(error_message)
                    last_digits = record.cil[22:]
                else:
                    error_message = _("Invalid CIL: The length is not correct")
                    raise ValidationError(error_message)

                # Check if the last 3 characters are numbers
                if not last_digits[-3:].isdigit():
                    error_message = _("Invalid CIL: Last 3 digits are not numbers")
                    raise ValidationError(error_message)

    @api.constrains("cadastral_reference")
    def _check_valid_cadastral_reference(self):
        for record in self:
            if record.cadastral_reference:
                try:
                    referenciacatastral.validate(self.cadastral_reference)
                except Exception as e:
                    error_message = _("Invalid Cadastral Reference: {error}").format(
                        error=e
                    )
                    raise ValidationError(error_message)


class CoefficientReport(models.TransientModel):
    _name = "energy_selfconsumption.coefficient_report"
    _description = "Generate Partition Coefficient Report"

    report_data = fields.Text("Report Data", readonly=True)
    file_name = fields.Char("File Name", readonly=True)
