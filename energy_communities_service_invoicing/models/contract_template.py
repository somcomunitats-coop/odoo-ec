from odoo import _, api, fields, models

from odoo.addons.energy_communities.config import (
    PACK_TYPE_PLATFORM_PRODUCT_CATEG_XML_ID,
)

from ..config import PACK_TYPE_PLATFORM


class ContractTemplate(models.Model):
    _name = "contract.template"
    _inherit = ["contract.template", "pack.type.mixin"]

    is_free_pack = fields.Boolean(string="Is a free pack")

    def custom_compute_pack_type(self):
        self._set_custom_pack_type_on_contract_template(
            PACK_TYPE_PLATFORM,
            PACK_TYPE_PLATFORM_PRODUCT_CATEG_XML_ID,
        )
