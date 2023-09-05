from odoo import api, fields, models


class Reseller(models.Model):
    _name = "energy_selfconsumption.reseller"
    _description = "Energy Reseller"

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
