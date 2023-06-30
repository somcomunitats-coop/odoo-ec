from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import base64
import logging
from io import StringIO
import chardet
from csv import reader

logger = logging.getLogger(__name__)


class DistributionTableImportWizard(models.TransientModel):
    _name = 'energy_selfconsumption.distribution_table_import.wizard'

    import_file = fields.Binary(string="Import File (*.csv)")
    fname = fields.Char(string="File Name")

    @api.constrains('import_file')
    def _constrains_import_file(self):
        format = str(self.fname.split(".")[1])
        if format != 'csv':
            raise ValidationError("Only csv format files are accepted.")

    def import_file_button(self):
        file_data = base64.b64decode(self.import_file)
        parsing_data = self.with_context(active_id=self.ids[0])._parse_file(file_data)
        active_id = self.env.context.get('active_id')
        distribution_table = self.env['energy_selfconsumption.distribution_table'].browse(active_id)
        parsing_errors = []
        self.import_all_lines(parsing_data, distribution_table)
        return True

    def _parse_file(self, data_file):
        self.ensure_one()
        try:
            csv_options = {}

            csv_options["delimiter"] = ','
            csv_options["quotechar"] = '"'
            try:
                decoded_file = data_file.decode("utf-8")
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
            {
                'supply_point_assignation_ids': supply_point_assignation_values_list
            }
        )

    def get_supply_point_assignation_values(self, line):
        return {
            'supply_point_id': self.get_supply_point_id(code=line[0]),
            'coefficient': self.get_coefficient(coefficient=line[1])
        }

    def get_supply_point_id(self, code):
        supply_point = self.env['energy_selfconsumption.supply_point'].search([('code', '=', code)])
        if not supply_point:
            return False
        return supply_point.id

    def get_coefficient(self, coefficient):
        try:
            return fields.Float.convert_to_write(self=fields.Float(), value=coefficient, record=self.env[
                'energy_selfconsumption.supply_point_assignation'].coefficient)
        except ValueError:
            return 0
