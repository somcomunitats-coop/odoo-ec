from odoo import api, fields, models


class Supplier(models.Model):
    _name = "energy_project.distributor"
    _description = "Energy Distributor"

    nif = fields.Char(string="NIF empresa", translate=False)
    order = fields.Char(string="Nº de orden", translate=False)
    name = fields.Char(string="Nombre empresa", translate=False)
    phone = fields.Char(string="Teléfono Att cliente gratuito", translate=False)
    portal = fields.Char(string="Portal de medidas", translate=False)

    def _load_records(self, data_list, update=False):
        new_data_list = []
        for data in data_list:
            values = data["values"]
            if values.get("order"):
                xml_id = "energy_project.distributor_%s" % (values.get("order"))
                new_data_list.append(dict(xml_id=xml_id, values=values, noupdate=True))
            else:
                new_data_list.append(data)
        return super()._load_records(new_data_list, update)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def button_open_distributors(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "energy_project.distributor",
            "view_mode": "tree,form",
            "target": "current",
        }
