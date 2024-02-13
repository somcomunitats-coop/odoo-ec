from odoo import api, fields, models


class CrmLeadMetadataMapping(models.Model):
    _name = "crm.lead.metadata.mapping"

    name = fields.Char(string="Name", compute="_compute_name")
    utm_source_ids = fields.One2many(
        "utm.source", "crm_lead_metadata_mapping_id", string="Related sources"
    )
    metadata_mapping_field_ids = fields.One2many(
        "crm.lead.metadata.mapping.field",
        "crm_lead_metadata_mapping_id",
        string="Related mapping fields",
    )

    @api.depends("utm_source_ids")
    def _compute_name(self):
        for record in self:
            name = ""
            for source in record.utm_source_ids:
                name += source.name
                if source.name != record.utm_source_ids[-1].name:
                    name += ", "
            record.name = name
