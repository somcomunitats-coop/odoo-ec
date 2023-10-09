from odoo import api, fields, models


class Supplier(models.Model):
    _name = "energy_project.supplier"
    _description = "Energy Supplier"

    """
    The string values are in spanish so it can be identified by Odoo when importing directly the CSV downloaded from the CNMC.
    This values can still be translated without problem.
    """
    nif = fields.Char(string="NIF empresa")
    order = fields.Char(string="Nº de orden")
    name = fields.Char(string="Nombre empresa")
    phone = fields.Char(string="Teléfono gratuito incidencias")
    portal = fields.Char(string="Portal de medidas")

    def _load_records(self, data_list, update=False):
        new_data_list = []
        for data in data_list:
            values = data["values"]
            if values.get("order"):
                xml_id = "energy_project.supplier_%s" % (values.get("order"))
                new_data_list.append(dict(xml_id=xml_id, values=values, noupdate=True))
            else:
                new_data_list.append(data)
        return super()._load_records(new_data_list, update)
