from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    lang = fields.Char(string="Language")


class CrmLeadTags(models.Model):
    _inherit = 'crm.lead.tag'

    tag_ext_id = fields.Char('ID Ext tag', compute='compute_ext_id_tag')

    def compute_ext_id_tag(self):
        for record in self:
            res = record.get_external_id()
            record.tag_ext_id = False
            if res.get(record.id):
                record.tag_ext_id = res.get(record.id)