import base64
import logging
from csv import reader
from io import StringIO

import chardet
import werkzeug

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
from stdnum.es import cups
from stdnum.exceptions import *

import math

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
        distribution_table.import_error_found = False
        type = distribution_table.type
        
        if type == 'variable_schedule':
            # For 'variable_schedule', queue job
            distribution_table.message_post(
                subject=_("Importation in Progress"),
                body=_("The distribution table import is being processed in the background. Any errors will be reported here."),
            )

            header, data_rows = parsing_data[0], parsing_data[1:]
            cups_groups = self._divide_in_groups(data_rows, 20) # Divide parsing_data in groups to optimized the memory use
            for group in cups_groups:
                # Add header before to process
                if distribution_table.import_error_found:
                    break
                group_with_header = [header] + group
                self.with_delay().process_variable_schedule(group_with_header, active_id)  
        else:
            # For other type, syncron type
            self.import_all_lines(parsing_data, distribution_table)
        return True

    def _divide_in_groups(self, data, group_size):
        """Divide the data into groups to process them separately."""
        return [data[i:i + group_size] for i in range(0, len(data), group_size)]

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
        supply_point_assignation_values_list = []

        for index, line in enumerate(data[1:]):
            value = self.get_supply_point_assignation_values(line)

            supply_point_assignation_values_list.append((0, 0, value))

            distribution_table.write(
                {"supply_point_assignation_ids": supply_point_assignation_values_list}
            )    
    
    def process_variable_schedule(self, data, distribution_table):
        DistributionTableVariable = self.env['energy_selfconsumption.distribution_table_variable']
        DistributionTableVariableCoefficient = self.env['energy_selfconsumption.distribution_table_var_coeff']
        cups_ids = data[0][1:]  # Get CUPS from header row
        logger.debug('CUPS IDs found: %s', cups_ids)
        # Validate CUPS before to process
        for cups in cups_ids:
            is_valid, error_message = self.validate_cups_id(cups, distribution_table)
            if not is_valid:
                logger.error(error_message)
                return
        hours_data = data[1:]  # The rest of the data contains hours and coefficients
        coefficients_batch = []
        batch_size = 50

        # Pre-search existing records to avoid repeated searches
        existing_variables = DistributionTableVariable.search([
            ('cups_id', 'in', cups_ids), 
            ('distribution_table_id', '=', distribution_table)
        ])
        existing_cups_map = {var.cups_id: var for var in existing_variables}
        logger.debug('Preloaded %d existing records from DistributionTableVariable', len(existing_variables))

        for row_index, row in enumerate(hours_data, start=1):
            hour = int(row[0])
            coefficients = list(map(float, row[1:]))  # Convert coefficients to float
            # Validate that the sum of coefficients is 1
            is_valid, error_message = self.validate_coefficients(coefficients, hour, distribution_table)
            if not is_valid:
                logger.error(error_message)
                return

            logger.debug('Processing data for time: %d', hour)
            for cups_index, coefficient in enumerate(row[1:], start=1):
                cups_id = cups_ids[cups_index - 1]
                variable_record = existing_cups_map.get(cups_id)
                if not variable_record:
                    variable_record = DistributionTableVariable.create({
                        'distribution_table_id': distribution_table,
                        'cups_id': cups_id,
                    })
                    existing_cups_map[cups_id] = variable_record
                    logger.debug('Created new DistributionTableVariable record for CUPS ID: %s', cups_id)

                coefficients_batch.append({
                    'distribution_table_variable_id': variable_record.id,
                    'hour': hour,
                    'coefficient': float(coefficient),
                })

            if len(coefficients_batch) >= batch_size:
                DistributionTableVariableCoefficient.create(coefficients_batch)
                logger.debug('Batch processing of %d coefficients for time %d', len(coefficients_batch), hour)
                coefficients_batch.clear()

        if coefficients_batch:
            DistributionTableVariableCoefficient.create(coefficients_batch)
            logger.debug('Processed last batch of %d coefficients', len(coefficients_batch))

        logger.debug('Completing the import process for the Distribution Table with ID: %s', distribution_table)

    def validate_cups_id(self, cups_id, distribution_table_id):
        try:
            cups.validate(cups_id)
            return True, ""
        except InvalidLength:
            error_message = _("Invalid CUPS %s: The length is incorrect." % (cups_id))
        except InvalidComponent:
            error_message = _("Invalid CUPS %s: The CUPS does not start with 'ES'." % (cups_id))
        except InvalidFormat:
            error_message = _("Invalid CUPS %s: The CUPS has an incorrect format." % (cups_id))
        except InvalidChecksum:
            error_message = _("Invalid CUPS %s: The checksum of the CUPS is incorrect." % (cups_id))

        distribution_table = self.env['energy_selfconsumption.distribution_table'].browse(distribution_table_id)
        message_status = distribution_table.message_post(
            subject=_("CUPS Validation Error"),
            body=error_message,
        )
        return False, error_message

    def validate_coefficients(self, coefficients, hour, distribution_table_id):
        total_sum = sum(coefficients)
        # Added tolerance margin to account for floating-point arithmetic imprecision.
        if not math.isclose(total_sum, 1.0, rel_tol=1e-9):
            error_message = _('The sum of coefficients for hour %s does not equal 1' % hour)
            distribution_table = self.env['energy_selfconsumption.distribution_table'].browse(distribution_table_id)
            message_status = distribution_table.message_post(
                subject=_("Coefficient Validation Error"),
                body=error_message,
            )
            distribution_table.import_error_found = True
            return False, error_message
        return True, ""

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
