from odoo import _, api, fields, models

from odoo.addons.energy_communities.config import (
    PACK_TYPE_NONE,
    PACK_TYPE_PLATFORM,
    PACK_TYPE_PLATFORM_PROD_CATEG_XMLID,
)


class ContractTemplate(models.Model):
    _name = "contract.template"
    _inherit = ["contract.template", "pack.type.mixin"]

    is_free_pack = fields.Boolean(string="Is a free pack")

    def _compute_pack_type(self):
        for record in self:
            record.pack_type = PACK_TYPE_NONE
            pack_product = self.env["product.template"].search(
                [
                    ("property_contract_template_id", "=", record.id),
                    ("is_contract", "=", True),
                ],
                limit=1,
            )
            if pack_product:
                record.pack_type = pack_product.pack_type
