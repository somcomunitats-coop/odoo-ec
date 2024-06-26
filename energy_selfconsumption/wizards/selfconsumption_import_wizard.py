import base64
import logging
import random
from csv import reader
from datetime import datetime
from io import StringIO

import chardet
from stdnum.es import iban

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class SelfconsumptionImportWizard(models.TransientModel):
    _name = "energy_selfconsumption.selfconsumption_import.wizard"

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
        for index, line in enumerate(parsing_data[1:], start=2):
            import_dict = self.get_line_dict(line)
            result = self.import_line(import_dict, project)
            if not result[0]:
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
        return {
            "partner_vat": line[0] or False,
            "effective_date": line[1] or False,
            "code": line[2] or False,
            "contracted_power": line[3] or False,
            "tariff": line[4] or False,
            "street": line[5] or False,
            "street2": line[6] or False,
            "city": line[7] or False,
            "state": line[8] or False,
            "postal_code": line[9] or False,
            "country": line[10] or False,
            "cadastral_reference": line[11] or False,
            "owner_vat": line[12] or False,
            "owner_firstname": line[13] or False,
            "owner_lastname": line[14] or False,
            "iban": line[15] or False,
            "mandate_auth_date": line[16] or False,
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
            csv = reader(StringIO(decoded_file), **csv_options)
            return list(csv)
        except BaseException:
            logger.warning("Parser error", exc_info=True)
            raise UserError(_("Error parsing the file"))

    def import_line(self, line_dict, project):
        if not line_dict["code"]:
            return False, _(
                "The CUPS field is required. Please make sure you provide a valid CUPS"
            )
        partner = self.env["res.partner"].search(
            [
                "|",
                ("vat", "=", line_dict["partner_vat"]),
                ("vat", "=ilike", line_dict["partner_vat"]),
            ],
            limit=1,
        )

        if not partner:
            return False, _("Partner with VAT:<b>{vat}</b> was not found.").format(
                vat=line_dict["partner_vat"]
            )
        if not line_dict["iban"]:
            return False, _("The IBAN field cannot be empty.")

        try:
            iban.validate(line_dict["iban"])
        except Exception as e:
            error_message = _("Invalid IBAN: {error}").format(error=e)
            raise ValidationError(error_message)

        bank_account = self.env["res.partner.bank"].search(
            [
                ("acc_number", "=", line_dict["iban"]),
                ("partner_id", "=", partner.id),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

        if not bank_account:
            bank_account = self.env["res.partner.bank"].create(
                {
                    "acc_number": line_dict["iban"],
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                }
            )
        try:
            mandate_auth_date = datetime.strptime(
                line_dict["mandate_auth_date"], self.date_format
            ).date()
            mandate = self.env["account.banking.mandate"].create(
                {
                    "format": "sepa",
                    "type": "recurrent",
                    "state": "valid",
                    "signature_date": mandate_auth_date,
                    "partner_bank_id": bank_account.id,
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                }
            )
        except Exception as e:
            return False, _("Could not create mandate for {vat}. {error}").format(
                vat=line_dict["partner_vat"], error=e
            )

        if not project.inscription_ids.filtered_domain(
            [("partner_id", "=", partner.id)]
        ):
            try:
                if line_dict["effective_date"]:
                    effective_date = datetime.strptime(
                        line_dict["effective_date"], self.date_format
                    ).date()
                else:
                    effective_date = fields.date.today()

                self.env["energy_project.inscription"].create(
                    {
                        "project_id": project.id,
                        "partner_id": partner.id,
                        "effective_date": effective_date,
                        "mandate_id": mandate.id,
                    }
                )
            except Exception as e:
                return False, _(
                    "Could not create inscription for {vat}. {error}"
                ).format(vat=line_dict["partner_vat"], error=e)

        supply_point = self.env["energy_selfconsumption.supply_point"].search(
            [("code", "=", line_dict["code"])]
        )

        if supply_point and supply_point.partner_id != partner:
            return False, _(
                "The supply point partner {supply_partner} and the partner {vat} in the inscription are different."
            ).format(supply_partner=supply_point.partner_id.vat, vat=partner.vat)

        if not supply_point:
            result = self.create_supply_point(line_dict, partner)
            if not result[0]:
                return result
        return True, False

    def create_supply_point(self, line_dict, partner):
        if line_dict["owner_vat"]:
            owner = self.env["res.partner"].search(
                [
                    "|",
                    ("vat", "=", line_dict["owner_vat"]),
                    ("vat", "=ilike", line_dict["owner_vat"]),
                ],
                limit=1,
            )
            if not owner:
                try:
                    owner = self.env["res.partner"].create(
                        {
                            "vat": line_dict["owner_vat"],
                            "firstname": line_dict["owner_firstname"],
                            "lastname": line_dict["owner_lastname"],
                            "company_type": "person",
                        }
                    )
                except Exception as e:
                    return False, _("Owner could not be created: {error}").format(
                        error=e
                    )
        else:
            owner = partner
        country = self.env["res.country"].search([("code", "=", line_dict["country"])])
        if not country:
            return False, _("Country code was not found: {country}").format(
                country=line_dict["country"]
            )
        state = self.env["res.country.state"].search(
            [("code", "=", line_dict["state"]), ("country_id", "=", country.id)]
        )
        if not state:
            return False, _("State code was not found: {state}").format(
                state=line_dict["state"]
            )

        return self.env["energy_selfconsumption.supply_point"].create(
            {
                "code": line_dict["code"],
                "name": line_dict["street"],
                "street": line_dict["street"],
                "street2": line_dict["street2"],
                "city": line_dict["city"],
                "zip": line_dict["postal_code"],
                "state_id": state.id,
                "country_id": country.id,
                "owner_id": owner.id,
                "partner_id": partner.id,
                "contracted_power": line_dict["contracted_power"],
                "tariff": line_dict["tariff"],
                "cadastral_reference": line_dict["cadastral_reference"],
            }
        )

        ###### This code is only for prubes

    def generar_iban_espanol(self):
        # Código de país y dígitos de control iniciales
        pais = "ES"
        digitos_control = "00"

        # Generar los 20 dígitos aleatorios
        digitos_aleatorios = "".join([str(random.randint(0, 9)) for _ in range(20)])

        # Concatenar todo para formar el IBAN
        iban = pais + digitos_control + digitos_aleatorios

        # Calcular el dígito de control
        d_control = str(98 - int(iban[2:]) % 97)

        # Ajustar el dígito de control si es necesario
        if len(d_control) == 1:
            d_control = "0" + d_control

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
                    "member": True,
                    "street": f"Calle imaginación {i}",
                    "city": "Madrid",
                    "zip": 28221,
                    "type": "contact",
                    "company_id": self.env.company.id,
                    # "company_type": "person",
                }
            )
            logger.info(f"\n\n Cliente creado {partner.name}")

            bank_account = self.env["res.partner.bank"].create(
                {
                    "acc_number": self.generar_iban_espanol(),
                    "partner_id": partner.id,
                    "company_id": self.env.company.id,
                }
            )

            logger.info(f"\n\n Cuenta del cliente creada {bank_account.acc_number}")

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

            logger.info(f"\n\n Mandato del cliente creado {mandate.id}")

            inscription = self.env["energy_project.inscription"].create(
                {
                    "project_id": active_id,
                    "partner_id": partner.id,
                    "effective_date": datetime.now().strftime("%Y-%m-%d"),
                    "mandate_id": mandate.id,
                }
            )

            logger.info(f"\n\n Incripción del cliente creada {inscription.id}")

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

            logger.info(f"\n\n Supply point del cliente creado {supply_point.id}")
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
                self.env["energy_project.inscription"].create(
                    {
                        "project_id": active_id,
                        "partner_id": partner.id,
                        "effective_date": datetime.now().strftime("%Y-%m-%d"),
                        "mandate_id": mandates[0].id,
                    }
                )
                count += 1

        return True
