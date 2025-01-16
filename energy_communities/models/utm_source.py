from odoo import fields, models


class UtmSource(models.Model):
    _inherit = "utm.source"

    source_ext_id = fields.Char(
        "ID Ext Source", compute="compute_ext_id_source", store=True
    )

    def compute_ext_id_source(self):
        for record in self:
            res = record.get_external_id()
            record.source_ext_id = False
            if res.get(record.id):
                record.source_ext_id = res.get(record.id)
