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

    def _get_default_community_wizard(self):
        creation_dict = super()._get_default_community_wizard()

        creation_dict.update(
            {
                "property_cooperator_account": self.env.ref(
                    "l10n_es.{}_account_common_4400".format(creation_dict["parent_id"])
                ).id,
                "product_share_template": self.env["product.template"]
                .search(
                    [
                        ("is_share", "=", True),
                        ("company_id", "=", creation_dict["parent_id"]),
                    ],
                    limit=1,
                )
                .id,
            }
        )
        return creation_dict
