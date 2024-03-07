import base64
import logging
from csv import reader
from io import StringIO

import chardet
import werkzeug

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.http import request


logger = logging.getLogger(__name__)


class DistributionTableImportWizard(models.TransientModel):
    _name = "energy_selfconsumption.distribution_table_import.wizard"

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
    
    @api.constrains("import_file")
    def _constrains_import_file(self):
        if self.fname:
            format = str(self.fname.split(".")[1])
            if format != "csv":
                raise ValidationError(_("Only csv format files are accepted."))

    def import_file_button(self):
        # Button to import file, checks whether it is necessary to enqueue or not according to the type field
        file_data = base64.b64decode(self.import_file)
        parsing_data = self.with_context(active_id=self.ids[0])._parse_file(file_data)
        active_id = self.env.context.get("active_id")
        distribution_table = self.env['energy_selfconsumption.distribution_table'].browse(active_id)
        
        type = distribution_table.type
        
        if type == 'variable_schedule':
            # For 'variable_schedule', queue job
            self.with_delay().import_all_lines(parsing_data, active_id)
            message = 'La importación de la programación variable se está procesando en segundo plano.'
        else:
            # For other type, syncron type
            self.import_all_lines(parsing_data, active_id)
            message = 'La importación ha finalizado.'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Importación Iniciada'),
                'message': message,
                'sticky': False,
            }
        }

    def download_template_button(self):
        type = self.env.context.get("type")
        if type == "fixed":
            template = (
                "energy_selfconsumption.distribution_table_fixed_example_attachment"
            )
        elif type == "variable_schedule":
            template = "energy_selfconsumption.distribution_table_variable_schedule_example_attachment"

        distribution_table_example_attachment = self.env.ref(template)
        download_url = "/web/content/{}/?download=true".format(
            str(distribution_table_example_attachment.id)
        )
        return {
            "type": "ir.actions.act_url",
            "url": download_url,
            "target": "new",
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

    def import_all_lines(self, data, distribution_table):
        logger.debug('Inicio de la importación para la Distribution Table con ID: %s', distribution_table)
        type = self.env['energy_selfconsumption.distribution_table'].browse(distribution_table).type
        logger.debug('El valor de type es: %s', type)
        if type == 'fixed':
            supply_point_assignation_values_list = []

            for index, line in enumerate(data[1:]):
                value = self.get_supply_point_assignation_values(line)

                supply_point_assignation_values_list.append((0, 0, value))

            distribution_table.write(
                {"supply_point_assignation_ids": supply_point_assignation_values_list}
            )
        elif type == 'variable_schedule':
            logger.debug('Procesando importación tipo "variable_schedule"')
            DistributionTableVariable = self.env['energy_selfconsumption.distribution_table_variable']
            DistributionTableVariableCoefficient = self.env['energy_selfconsumption.distribution_table_var_coeff']
            cups_ids = data[0][1:]  # Get CUPS
            logger.debug('CUPS IDs encontrados: %s', cups_ids)
            hours_data = data[1:]  # Get hours and coefficients

            for cups_index, cups_id in enumerate(cups_ids, start=1):
                # Create or find the record in DistributionTableVariable for the current CUPS
                logger.debug('Procesando CUPS ID: %s', cups_id)
                # Check if record exist
                variable_record = DistributionTableVariable.search([
                    ('distribution_table_id', '=', distribution_table),
                    ('cups_id', '=', cups_id),
                ], limit=1)

                # If not exist, create
                if not variable_record:
                    variable_record = DistributionTableVariable.create({
                        'distribution_table_id': distribution_table,
                        'cups_id': cups_id,
                    })

                # Proccess every hour and coefficient for this CUPS
                for row in hours_data:
                    hour = int(row[0])
                    coefficient = float(row[cups_index])  # Get the coefficient for the current hour and CUPS
                    logger.debug('Añadiendo coeficiente %s para la hora %s del CUPS ID: %s', coefficient, hour, cups_id)
                    # Create the coefficient record
                    DistributionTableVariableCoefficient.create({
                        'distribution_table_variable_id': variable_record.id,
                        'hour': hour,
                        'coefficient': coefficient,
                    })
        logger.debug('Finalización de la importación para la Distribution Table con ID: %s', distribution_table)

    def get_supply_point_assignation_values(self, line):
        return {
            "supply_point_id": self.get_supply_point_id(code=line[0]),
            "coefficient": self.get_coefficient(coefficient=line[1]),
        }

    def get_supply_point_id(self, code):
        supply_point_id = self.env["energy_selfconsumption.supply_point"].search_read(
            [("code", "=", code)], ["id"]
        )
        if not supply_point_id:
            raise ValidationError(
                _("There isn't any supply point with this code: {code}").format(
                    code=code
                )
            )
        return supply_point_id[0]["id"]

    def get_coefficient(self, coefficient):
        try:
            return fields.Float.convert_to_write(
                self=fields.Float(),
                value=coefficient,
                record=self.env[
                    "energy_selfconsumption.supply_point_assignation"
                ].coefficient,
            )
        except ValueError:
            return 0
