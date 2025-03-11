from odoo import _, api, fields, models


class ContractTemplate(models.Model):
    _name = "contract.template"
    _inherit = ["contract.template", "pack.type.mixin"]

    is_free_pack = fields.Boolean(string="Is a free pack")

    def custom_compute_pack_type(self):
        self._set_custom_pack_type_on_contract_template(
            "platform_pack",
            "energy_communities_service_invoicing.product_category_platform_pack",
        )
