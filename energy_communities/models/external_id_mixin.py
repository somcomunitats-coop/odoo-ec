import hashlib

from odoo import api, fields, models


class ExternalIdMixin(models.AbstractModel):
    _name = "external.id.mixin"
    _description = "External ID Mixin"

    external_id = fields.Char(
        string="External ID", compute="_compute_external_id", store=True
    )

    @api.depends("name")
    def _compute_external_id(self):
        for record in self:
            record.external_id = hashlib.sha1(str(record.id).encode()).hexdigest()
