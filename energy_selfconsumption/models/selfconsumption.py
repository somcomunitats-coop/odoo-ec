from datetime import datetime, timedelta

from stdnum.es import cups, referenciacatastral
from stdnum.exceptions import *

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

import random
import logging

_logger = logging.getLogger(__name__)


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
        default_type = (
            "hourly" if self.invoicing_mode == "energy_delivered_variable" else "fixed"
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Distribution Tables",
            "view_mode": "tree,form",
            "res_model": "energy_selfconsumption.distribution_table",
            "domain": [("selfconsumption_project_id", "=", self.id)],
            "context": {
                "create": True,
                "default_selfconsumption_project_id": self.id,
                "default_type": default_type,
            },
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
        if self.report_distribution_table:
            sql = f"""
                select dt.type,sp.code,spa.hour,spa.coefficient 
                from energy_selfconsumption_distribution_table as dt
                    inner join energy_selfconsumption_supply_point_assignation as spa 
                        on spa.distribution_table_id = dt.id
                    inner join energy_selfconsumption_supply_point as sp 
                        on sp.id = spa.supply_point_id
                        where dt.id={self.report_distribution_table.id};
            """
            self.env.cr.execute(sql)
            file_content = ""
            report_data = self.env.cr.fetchall()
            for i, record in enumerate(report_data):
                line = ""
                coefficient_format = f"{record[3]:.6f}"
                if record[0] == "hourly":
                    line = f"{record[1]};{record[2]};{coefficient_format.replace('.', ',')}"
                else:
                    line = f"{record[1]};{coefficient_format.replace('.', ',')}"

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

    def set_autogenerate_inscriptions(self):
        partners_socios = self.env["res.partner"].search([('member','=','True')],
                                                         limit=500)
        for partner in partners_socios:
            mandates = self.env["account.banking.mandate"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", partner.company_id.id),
                    ("state", "=", "valid"),
                ]
            )
            if mandates:
                self.env['energy_project.inscription'].create({
                    "project_id": self.project_id.id,
                    "partner_id": partner.id,
                    "effective_date": datetime.now().strftime("%Y-%m-%d"),
                    "mandate_id": mandates[0].id,
                })

        return True

    def generar_iban_espanol(self):
        # Código de país y dígitos de control iniciales
        pais = "ES"
        digitos_control = "00"

        # Generar los 20 dígitos aleatorios
        digitos_aleatorios = ''.join([str(random.randint(0, 9)) for _ in range(20)])

        # Concatenar todo para formar el IBAN
        iban = pais + digitos_control + digitos_aleatorios

        # Calcular el dígito de control
        d_control = str(98 - int(iban[2:]) % 97)

        # Ajustar el dígito de control si es necesario
        if len(d_control) == 1:
            d_control = '0' + d_control

        # Reemplazar los dígitos de control iniciales con el dígito de control calculado
        iban = pais + d_control + digitos_aleatorios

        return iban

    def generar_vat_espanol(self):
        letras_nif = "TRWAGMYFPDXBNJZSQVHLCKE"
        numero = str(random.randint(0, 99999999)).zfill(8)
        letra = letras_nif[int(numero) % 23]
        return numero + letra

    def generate_cups(self):
        alphabet = "TRWAGMYFPDXBNJZSQVHLCKE"

        def generate_numeric_part():
            distributor = "1234"
            supply_number = str(random.randint(0, 999999999999)).zfill(12)
            return distributor + supply_number

        def calculate_control_characters(numeric_part):
            integer_number = int(numeric_part)
            # Calculate the remainder of dividing the integer by 529
            # This remainder is used to determine the control characters
            R0 = integer_number % 529
            # Divide R0 by 23 and use integer division to get the index of the first control character
            C = R0 // 23
            # Use the remainder of dividing R0 by 23 to get the index of the second control character
            R = R0 % 23
            return alphabet[C] + alphabet[R]

        numeric_part = generate_numeric_part()
        control_characters = calculate_control_characters(numeric_part)
        formatted_cups = f"ES{numeric_part}{control_characters}"
        return formatted_cups

    def set_autogenerate_inscriptions_mandataris_supply_points(self):
        for i in range(0, 500):
            _logger.info(f"\n\n Creando el cliente número {i}")
            country_id = self.env["res.country"].search([("code", "=", "ES")]
                                                        )[0].id
            vat = self.generar_vat_espanol()
            partner = self.env["res.partner"].create({
                "name": f"Prueba {vat} {i}",
                "vat": vat,
                "country_id": country_id,
                "state_id": self.env["res.country.state"].search(
                    [("code", "=", 'MA'), ("country_id", "=", country_id)]
                )[0].id,
                "member": True,
                "street": f"Calle imaginación {i}",
                "city": "Madrid",
                "zip": 28221,
                "type": "contact",
                "company_id": self.env.company.id,
                # "company_type": "person",
            })
            _logger.info(f"\n\n Cliente creado {partner.name}")

            bank_account = self.env["res.partner.bank"].create(
                {
                    "acc_number": self.generar_iban_espanol(),
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                }
            )

            _logger.info(f"\n\n Cuenta del cliente creada {bank_account.acc_number}")

            mandate = self.env["account.banking.mandate"].create(
                {
                    "format": "sepa",
                    "type": "recurrent",
                    "state": "valid",
                    "signature_date": datetime.now().strftime("%Y-%m-%d"),
                    "partner_bank_id": bank_account.id,
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                }
            )

            _logger.info(f"\n\n Mandato del cliente creado {mandate.id}")

            inscription = self.env['energy_project.inscription'].create({
                "project_id": self.project_id.id,
                "partner_id": partner.id,
                "effective_date": datetime.now().strftime("%Y-%m-%d"),
                "mandate_id": mandate.id,
            })

            _logger.info(f"\n\n Incripción del cliente creada {inscription.id}")

            _ACCESS_TARIFF_VALUES = [
                ("6.1TD", "6.1TD"),
                ("6.2TD", "6.2TD"),
                ("6.3TD", "6.3TD"),
                ("6.4TD", "6.4TD"),
            ]

            contracted_power = round(random.uniform(1, 100), 2)

            if contracted_power <= 15:
                tariff = "2.0TD"
            elif contracted_power <= 50:
                tariff = "3.0TD"
            else:
                tariff = random.choice(_ACCESS_TARIFF_VALUES)[0]

            supply_point = self.env["energy_selfconsumption.supply_point"].create(
                {
                    "code": self.generate_cups(),
                    "name": partner.street,
                    "street": partner.street,
                    "city": partner.city,
                    "zip": partner.zip,
                    "state_id": partner.state_id.id,
                    "country_id": partner.country_id.id,
                    "owner_id": partner.id,
                    "partner_id": partner.id,
                    "contracted_power": contracted_power,
                    "tariff": tariff
                }
            )

            _logger.info(f"\n\n Supply point del cliente creado {supply_point.id}")
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
