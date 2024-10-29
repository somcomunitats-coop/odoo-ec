from odoo import fields, models


class UtmSource(models.Model):
    _inherit = "utm.source"

    crm_lead_metadata_mapping_id = fields.Many2one("crm.lead.metadata.mapping")
    crm_team_id = fields.Many2one("crm.team", string="Sales team for this source")
