from odoo import fields, models


class CmCoordinatesMixin(models.AbstractModel):
    _name = "cm.coordinates.mixin"
    _description = "Add map coordinates to any model"

    lat = fields.Char(string="Latitude")
    lng = fields.Char(string="Longitude")
