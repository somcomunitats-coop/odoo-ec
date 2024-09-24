from odoo import _, api, fields, models


class EnergyAction(models.Model):
    _name = "energy.action"

    name = fields.Char(string="Name")
    xml_id = fields.Char(compute="_compute_xml_id", string="External ID")

    def _compute_xml_id(self):
        res = self.get_external_id()
        for record in self:
            record.xml_id = res.get(record.id)
