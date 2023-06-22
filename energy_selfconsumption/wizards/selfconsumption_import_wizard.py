from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
import base64
import logging
from io import StringIO
import chardet
from csv import reader

logger = logging.getLogger(__name__)


class SelfconsumptionImportWizard(models.TransientModel):
    _name = 'energy_selfconsumption.selfconsumption_import.wizard'

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
        project = self.env['energy_selfconsumption.selfconsumption'].browse(active_id)
        # check exist distribution table
        distribution_table = self.env['energy_selfconsumption.distribution_table'].create({
            'selfconsumption_project_id': project.id
        })

        for index, single_statement_data in enumerate(parsing_data):
            self.import_single_statement(single_statement_data, distribution_table)
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
            return csv
        except BaseException:
            logger.warning("Parser error", exc_info=True)
            raise UserError(_("Error parsing the file"))

    def import_single_statement(self, line, distribution_table):
        supply_point = self.env['energy_selfconsumption.supply_point'].search([('code', '=', line[0])])
        if not supply_point:
            supply_point = self.create_supply_point(
                code=line[0],
                street=line[2],
                street2=line[3],
                city=line[4],
                state=line[5],
                zip=line[6],
                country=line[7],
                owner_vat=line[9]
            )

        self.env['energy_selfconsumption.supply_point_assignation'].create({
            'supply_point_id': supply_point.id,
            'distribution_table_id': distribution_table.id,
            'coefficient': line[1]
        })

    def create_supply_point(self, code, street, street2, city, state, zip, country, owner_vat):
        owner = self.env['res.partner'].search([('vat', '=', owner_vat)])
        if not owner:
            # TODO create new owner
            raise UserError('Owner not found VAT:{}'.format(owner_vat))
        country = self.env['res.country'].search([('code', '=', country)])
        return self.env['energy_selfconsumption.supply_point'].create({
            'code': code,
            'name': code,
            'street': street,
            'street2': street2,
            'city': city,
            'state_id': self.env['res.country.state'].search([('code', '=', state), ('country_id', '=', country.id)]).id,
            'zip': zip,
            'country_id': country.id,
            'owner_id': owner.id,
            'cooperator_id': owner.id #TODO move it to other module
        })


