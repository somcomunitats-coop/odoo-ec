from odoo import api, fields, models


class Reseller(models.Model):
    _name = "energy_selfconsumption.reseller"
    _description = "Energy Reseller"

    order = fields.Char(string="Nº de orden", required=True)
    name = fields.Char(string="Nombre empresa")
    address = fields.Char(string="Dirección empresa")
    zip = fields.Char(string="C.P.")
    city = fields.Char(string="Municipio empresa")
    province = fields.Char(string="Provincia empresa")
    phone = fields.Char(string="Teléfono Att cliente gratuito")
    scope = fields.Char(string="Ámbito actuación")
    vat = fields.Char(string="NIF empresa")
    inscription_date = fields.Date(string="Fecha alta")
    uninscription_date = fields.Date(string="Fecha baja")
    web = fields.Char(string="Página web")
    state = fields.Char(string="Estado")

    def _load_records(self, data_list, update=False):
        new_data_list = []
        for data in data_list:
            values = data["values"]
            if values.get("order"):
                xml_id = "energy_selfconsumption.reseller_%s" % (values.get("order"))
                new_data_list.append(
                    dict(xml_id=xml_id, values=values, noupdate=data.get("noupdate"))
                )
        return super()._load_records(new_data_list, update)
