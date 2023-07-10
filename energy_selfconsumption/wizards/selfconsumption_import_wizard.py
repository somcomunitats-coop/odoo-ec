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
    delimiter = fields.Char(default=',', required=True, string='File Delimiter', help='Delimiter in import CSV file.')
    quotechar = fields.Char(default='"', required=True, string='File Quotechar', help='Quotechar in import CSV file.')
    encoding = fields.Char(default='utf-8', required=True, string='File Encoding', help='Enconding format in import CSV file.')

    @api.constrains('import_file')
    def _constrains_import_file(self):
        format = str(self.fname.split(".")[1])
        if format != 'csv':
            raise ValidationError("Only csv format files are accepted.")

    def import_file_button(self):
        error_string_list = ''
        file_data = base64.b64decode(self.import_file)
        parsing_data = self.with_context(active_id=self.ids[0])._parse_file(file_data)
        active_id = self.env.context.get('active_id')
        project = self.env['energy_selfconsumption.selfconsumption'].browse(active_id)
        for index, line in enumerate(parsing_data[1:]):
            import_dict = self.get_line_dict(line)
            error = self.import_line(import_dict, project)
            if error[0]:
                error_string_list = "".join(
                    [error_string_list, _('<li>Line {line}: {error}</li>\n').format(index, error[1])])
        if error_string_list:
            project.message_post(subject=_('Import Errors'),
                                 body=_('Import errors found: <ul>{list}</ul>'.format(list=error_string_list)))
        return True

    def get_line_dict(self, line):
        return {
            'partner_vat': line[0] or False,
            'effective_date': line[1] or False,
            'code': line[2] or False,
            'street1': line[3] or False,
            'street2': line[4] or False,
            'city': line[5] or False,
            'state': line[6] or False,
            'postal_code': line[7] or False,
            'country': line[8] or False,
            'owner_vat': line[9] or False,
            'owner_firstname': line[10] or False,
            'owner_lastname': line[11] or False,
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
        partner = self.env['res.partner'].search([
            '|', ('vat', '=', line_dict['partner_vat']), ('vat', '=ilike', line_dict['partner_vat'])
        ], limit=1)

        if not partner:
            return False, _('Partner with VAT:<b>{vat}</b> was not found.').format(vat=line_dict['partner_vat'])

        if not project.inscription_ids.filtered_domain([('partner_id', '=', partner.id)]):
            try:
                self.env['energy_project.inscription'].create({
                    'project_id': project.id,
                    'partner_id': partner.id,
                    'effective_date': fields.date.today()
                })
            except:
                return False, _('Could not create inscription for {vat}.').format(vat=line_dict['partner_vat'])

        supply_point = self.env['energy_selfconsumption.supply_point'].search([('code', '=', line_dict['code'])])

        if supply_point and supply_point.partner_id != partner:
            return False, _(
                'The supply point partner {supply_partner} and the partner {vat} in the subscription are different.').format(
                supply_partner=supply_point.partner_id.vat, vat=partner.vat)

        return False

    def create_supply_point(self, code, street, street2, city, state, zip, country, owner_vat):
        owner = self.env['res.partner'].search([
            '|', ('vat', '=', owner_vat), ('vat', '=ilike', owner_vat)
        ], limit=1)
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
