from odoo import api, fields, models


class Reseller(models.Model):
    _name = "energy_project.reseller"
    _description = "Energy Reseller"

    """
    The string values are in spanish so it can be identified by Odoo when importing directly the CSV downloaded from the CNMC.
    This values can be still be translated without problem.
    """
    order = fields.Char(string="Nº de orden")
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
                xml_id = "energy_project.reseller_%s" % (values.get("order"))
                new_data_list.append(dict(xml_id=xml_id, values=values, noupdate=True))
            else:
                new_data_list.append(data)
        return super()._load_records(new_data_list, update)
