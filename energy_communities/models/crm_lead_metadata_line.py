from odoo import fields, models


class CrmLeadMetadataLine(models.Model):
    _name = "crm.lead.metadata.line"
    _inherit = "crm.lead.metadata.line"

    value = fields.Char(translate=False)
