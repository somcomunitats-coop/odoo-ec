import base64
import logging
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
