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
        parsing_errors = []
        for index, single_statement_data in enumerate(parsing_data[1:]):
            found = self.import_single_statement(single_statement_data, project)
            if not found:
                parsing_errors.append((index, single_statement_data))
        if parsing_errors:
            error_list = ''
            for error in parsing_errors:
                error_list = "".join(
                    [error_list, _('<li>Line: {index} DNI: {vat} </li>\n').format(index=error[0], vat=error[1][0])])
            project.message_post(subject=_('Import Result'),
                                 body=_('Partners not found for: <ul>{list}</ul>'.format(list=error_list)))
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

    def import_single_statement(self, line, project):
        partner = self.env['res.partner'].search([
            ('vat', '=ilike', line[0])
        ], limit=1)

        if not partner:
            if line[2]:
                partner = self.env['res.partner'].create({
                    'vat': line[0],
                    'firstname': line[2],
                    'lastname': line[3],
                    'company_type': 'person'
                })
            else:
                return False
        if partner.id in project.inscription_ids.mapped('partner_id.id'):
            return False
        try:
            self.env['energy_project.inscription'].create({
                'project_id': project.id,
                'partner_id': partner.id,
                'effective_date': fields.date.today()
            }
            )
        except:
            return False
        return True

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
            'state_id': self.env['res.country.state'].search(
                [('code', '=', state), ('country_id', '=', country.id)]).id,
            'zip': zip,
            'country_id': country.id,
            'owner_id': owner.id,
            'partner_id': partner.id
        })
