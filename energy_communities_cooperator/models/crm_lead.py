from odoo import models


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = "crm.lead"

    def _get_metadata_values(self):
        metadata = super()._get_metadata_values()
        capital_share_meta_entry = self.metadata_line_ids.filtered(
            lambda meta: meta.key == "ce_member_mandatory_contribution"
        )
        if capital_share_meta_entry:
            metadata["capital_share"] = capital_share_meta_entry.value
        return metadata
