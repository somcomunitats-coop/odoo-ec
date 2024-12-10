import base64
import logging
import random
from csv import DictReader
from datetime import datetime
from io import StringIO

import chardet

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class SelfconsumptionImportWizard(models.TransientModel):
    _name = "energy_selfconsumption.selfconsumption_import.wizard"
    _description = "Service to import project selfconsumption"

    import_file = fields.Binary(string="Import File (*.csv)")
    fname = fields.Char(string="File Name")
    delimiter = fields.Char(
        default=",",
        required=True,
        string="File Delimiter",
        help="Delimiter in import CSV file.",
    )
    quotechar = fields.Char(
        default='"',
        required=True,
        string="File Quotechar",
        help="Quotechar in import CSV file.",
    )
    encoding = fields.Char(
        default="utf-8",
        required=True,
        string="File Encoding",
        help="Enconding format in import CSV file.",
    )
    date_format = fields.Char(
        default="%d/%m/%Y",
        required=True,
        string="Date Format",
        help="Date format for effective date.",
    )

    user_current_role = fields.Char()

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)
        defaults["user_current_role"] = self.env.user.user_current_role
        return defaults

    @api.constrains("import_file")
    def _constrains_import_file(self):
        if self.fname:
            format = str(self.fname.split(".")[1])
            if format != "csv":
                raise ValidationError(_("Only csv format files are accepted."))

    def import_file_button(self):
        self.flush()
        error_string_list = ""
        file_data = base64.b64decode(self.import_file)
        parsing_data = self.with_context(active_id=self.ids[0])._parse_file(file_data)
        active_id = self.env.context.get("active_id")
        project = self.env["energy_selfconsumption.selfconsumption"].browse(active_id)
        for index, line in enumerate(parsing_data):
            import_dict = self.get_line_dict(line)
            result = self.import_line(import_dict, project)
            if result[0]:
                error_string_list = "".join(
                    [
                        error_string_list,
                        _("<li>Line {line}: {error}</li>\n").format(
                            line=index, error=result[1]
                        ),
                    ]
                )
        if error_string_list:
            project.message_post(
                subject=_("Import Errors"),
                body=_("Import errors found: <ul>{list}</ul>").format(
                    list=error_string_list
                ),
            )
        return True

    def download_template_button(self):
        distribution_table_example_attachment = self.env.ref(
            "energy_selfconsumption.selfconsumption_table_example_attachment"
        )
        download_url = "/web/content/{}/?download=true".format(
            str(distribution_table_example_attachment.id)
        )
        return {
            "type": "ir.actions.act_url",
            "url": download_url,
            "target": "new",
        }

    def download_list_button(self):
        list_state_attachment = self.env.ref(
            "energy_selfconsumption.list_state_attachment"
        )
        download_url = "/web/content/{}/?download=true".format(
            str(list_state_attachment.id)
        )
        return {
            "type": "ir.actions.act_url",
            "url": download_url,
            "target": "new",
        }

    def get_line_dict(self, line):
        header = list(line.keys())
        if len(header) != 17:
            raise ValidationError(
                _(
                    "The file should contain 17 columns and not {header_length} columns."
                ).format(header_length=len(header))
            )
        supplypoint_owner_id_same = "no"
        if not line.get(header[12], False):
            supplypoint_owner_id_same = "yes"
        if not line.get(header[13], False):
            supplypoint_owner_id_same = "yes"
        if not line.get(header[14], False):
            supplypoint_owner_id_same = "yes"
        return {
            "inscription_partner_id_vat": line.get(header[0], False),
            "effective_date": line.get(header[1], False),
            "supplypoint_cups": line.get(header[2], False),
            "supplypoint_contracted_power": float(
                str(line.get(header[3], 0.0)).replace(",", ".")
            ),
            "tariff": line.get(header[4], False),
            "supplypoint_street": line.get(header[5], False),
            "street2": line.get(header[6], False),
            "supplypoint_city": line.get(header[7], False),
            "state": line.get(header[8], False),
            "supplypoint_zip": line.get(header[9], False),
            "country": line.get(header[10], False),
            "supplypoint_cadastral_reference": line.get(header[11], False),
            "supplypoint_owner_id_vat": line.get(header[12], False),
            "supplypoint_owner_id_name": line.get(header[13], False),
            "supplypoint_owner_id_lastname": line.get(header[14], False),
            "inscription_acc_number": line.get(header[15], False),
            "mandate_auth_date": line.get(header[16], False),
            "date_format": self.date_format,
            "supplypoint_owner_id_same": supplypoint_owner_id_same,
        }

    def _parse_file(self, data_file):
        self.ensure_one()
        try:
            csv_options = {}

            csv_options["delimiter"] = self.delimiter
            csv_options["quotechar"] = self.quotechar
            try:
                decoded_file = data_file.decode(self.encoding)
            except UnicodeDecodeError:
                detected_encoding = chardet.detect(data_file).get("encoding", False)
                if not detected_encoding:
                    raise UserError(
                        _("No valid encoding was found for the attached file")
                    )
                decoded_file = data_file.decode(detected_encoding)
            csv_file = StringIO(decoded_file)
            csv = DictReader(csv_file, **csv_options)
            return list(csv)
        except BaseException:
            logger.warning("Parser error", exc_info=True)
            raise UserError(_("Error parsing the file"))

    def import_line(self, line_dict, project):
        return (
            self.env["energy_selfconsumption.create_inscription_selfconsumption"]
            .sudo()
            .create_inscription(
                line_dict,
                project,
            )
        )

    ###### This code is only for prubes

    def generar_iban_espanol(self):
        # Country code and initial check digits
        pais = "ES"
        digitos_control = "00"

        # Generate the 20 random digits
        digitos_aleatorios = "".join([str(random.randint(0, 9)) for _ in range(20)])

        # Concatenate all to form the IBAN
        iban = pais + digitos_control + digitos_aleatorios

        # Calculate the check digit
        d_control = str(98 - int(iban[2:]) % 97)

        # Adjust the check digit if necessary.
        if len(d_control) == 1:
            d_control = "0" + d_control

        # Replace the initial check digits with the calculated check digit.
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
        active_id = self.env.context.get("active_id")
        logger.info(f"\n\n set_autogenerate_inscriptions_mandataris_supply_points")
        for i in range(0, 500):
            logger.info(f"\n\n Creando el cliente número {i}")
            country_id = self.env["res.country"].search([("code", "=", "ES")])[0].id
            vat = self.generar_vat_espanol()
            partner = self.env["res.partner"].create(
                {
                    "name": f"Prueba {vat} {i}",
                    "vat": vat,
                    "country_id": country_id,
                    "state_id": self.env["res.country.state"]
                    .search([("code", "=", "MA"), ("country_id", "=", country_id)])[0]
                    .id,
                    "street": f"Calle imaginación {i}",
                    "city": "Madrid",
                    "zip": 28221,
                    "type": "contact",
                    "company_id": self.env.company.id,
                    "company_type": "person",
                    "cooperative_membership_id": self.env.company.partner_id.id,
                }
            )

            bank_account = self.env["res.partner.bank"].create(
                {
                    "acc_number": self.generar_iban_espanol(),
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                }
            )

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

            participation = (
                self.env["energy_project.participation"]
                .sudo()
                .search(
                    [
                        (
                            "project_id",
                            "=",
                            active_id,
                        )
                    ]
                )
            )

            if not participation:
                raise ValidationError(_("Dont exit participation for this project."))

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
                    "tariff": tariff,
                }
            )

            self.env["energy_selfconsumption.inscription_selfconsumption"].create(
                {
                    "project_id": active_id,
                    "partner_id": partner.id,
                    "effective_date": datetime.now().strftime("%Y-%m-%d"),
                    "mandate_id": mandate.id,
                    "supply_point_id": supply_point.id,
                    "participation": participation[0].id,
                    "annual_electricity_use": 1.0,
                    "accept": True,
                    "member": True,
                }
            )
        return True

    def set_autogenerate_inscriptions(self):
        active_id = self.env.context.get("active_id")
        logger.info(f"\n\n set_autogenerate_inscriptions")
        partners_socios = self.env["res.partner"].search([("name", "like", "Prueba %")])
        count = 0
        for partner in partners_socios:
            if count == 500:
                break
            mandates = self.env["account.banking.mandate"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", partner.company_id.id),
                    ("state", "=", "valid"),
                ]
            )
            if mandates:
                participation = (
                    self.env["energy_project.participation"]
                    .sudo()
                    .search(
                        [
                            (
                                "project_id",
                                "=",
                                active_id,
                            )
                        ]
                    )
                )
                if participation:
                    self.env[
                        "energy_selfconsumption.inscription_selfconsumption"
                    ].create(
                        {
                            "project_id": active_id,
                            "partner_id": partner.id,
                            "effective_date": datetime.now().strftime("%Y-%m-%d"),
                            "mandate_id": mandates[0].id,
                            "code": self.generate_cups(),
                            "participation": participation[0].id,
                            "annual_electricity_use": 1.0,
                            "accept": True,
                            "member": True,
                        }
                    )
                    count += 1

        return True
