from odoo import models, fields, _
from odoo.exceptions import ValidationError
import base64
import csv
from io import StringIO

class ExportCsvInscriptionsWizard(models.TransientModel):
    _name = "export.csv.inscritions.wizard"
    _description = "Asistente para exportar CSV"

    file_data = fields.Binary("File CSV", readonly=True)
    file_name = fields.Char("Name file", readonly=True)

    def exportar_csv(self):
        output = StringIO()
        writer = csv.writer(output, delimiter=';')

        selfconsumption = self.env["energy_selfconsumption.selfconsumption"].browse(self.env.context.get("active_id", False))

        if not selfconsumption:
            raise ValidationError("Need a selfconsumption project")
        
        inscriptions = selfconsumption.inscription_ids

        if not inscriptions:
            raise ValidationError("No inscriptions found")

        # Encabezados
        headers = [
            "DNI Socio", "Fecha efectiva", "CUPS", "Potencia máxima contratada", "Tarifa de acceso",
            "Calle 1", "Calle 2", "Ciudad", "Provincia", "Código postal", "Código ISO del país",
            "Referencia Catastral", "DNI Titular", "Nombre Titular", "Apellidos Titular",
            "Género Titular", "Fecha nacimiento Titular", "Teléfono Titular", "Idioma Titular",
            "Email Titular", "Situación vulnerabilidad Titular", "Acepta política privacidad Titular",
            "IBAN", "Fecha autorización cargo bancario del mandato", "Usa auto-consumo",
            "Uso consumo eléctrico anual", "Participación", "Acepta Términos"
        ]
        writer.writerow(headers)

        for inscription in inscriptions:
            writer.writerow([
                inscription.partner_id.vat or '',
                inscription.effective_date.strftime('%d/%m/%Y') or '',
                inscription.supply_point_id.code if inscription.supply_point_id and inscription.supply_point_id.code else '',
                inscription.supply_point_id.contracted_power if inscription.supply_point_id and inscription.supply_point_id.contracted_power else '',
                inscription.supply_point_id.tariff if inscription.supply_point_id and inscription.supply_point_id.tariff else '',
                inscription.supply_point_id.street if inscription.supply_point_id and inscription.supply_point_id.street else '',
                '',
                inscription.supply_point_id.city if inscription.supply_point_id and inscription.supply_point_id.city else '',
                inscription.supply_point_id.state_id.name if inscription.supply_point_id and inscription.supply_point_id.state_id else '',
                inscription.supply_point_id.zip if inscription.supply_point_id and inscription.supply_point_id.zip else '',
                inscription.supply_point_id.country_id.code if inscription.supply_point_id and inscription.supply_point_id.country_id else '',
                inscription.supply_point_id.cadastral_reference if inscription.supply_point_id and inscription.supply_point_id.cadastral_reference else '',
                inscription.owner_id.vat if inscription.owner_id and inscription.owner_id.vat else '',
                inscription.owner_id.name if inscription.owner_id and inscription.owner_id.name else '',
                inscription.owner_id.lastname if inscription.owner_id and inscription.owner_id.lastname else '',
                inscription.owner_id.gender if inscription.owner_id and inscription.owner_id.gender else '',
                inscription.owner_id.birthdate_date.strftime('%d/%m/%Y') if inscription.owner_id and inscription.owner_id.birthdate_date else '',
                inscription.owner_id.phone if inscription.owner_id and inscription.owner_id.phone else '',
                inscription.owner_id.lang if inscription.owner_id and inscription.owner_id.lang else '',
                inscription.owner_id.email if inscription.owner_id and inscription.owner_id.email else '',
                inscription.owner_id.vulnerability_situation if inscription.owner_id and inscription.owner_id.vulnerability_situation else '',
                'yes',
                inscription.acc_number or '',
                inscription.mandate_id.signature_date.strftime('%d/%m/%Y') if inscription.mandate_id and inscription.mandate_id.signature_date else '',
                inscription.supply_point_id.used_in_selfconsumption if inscription.supply_point_id and inscription.supply_point_id.used_in_selfconsumption else '',
                inscription.annual_electricity_use or '',
                inscription.participation_quantity or '',
                'yes',
            ])

        csv_data = output.getvalue().encode('utf-8')
        output.close()

        self.write({
            'file_data': base64.b64encode(csv_data),
            'file_name': _('export_inscriptions.csv')
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.csv.inscritions.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }