from odoo import _, api, fields, models


class ContractTemplate(models.Model):
    _name = "contract.template"
    _inherit = ["contract.template", "pack.type.mixin"]

    def custom_compute_pack_type(self):
        super().custom_compute_pack_type()
        if self.pack_type == "none":
            self._set_custom_pack_type_on_contract_template(
                "selfconsumption_pack",
                "energy_selfconsumption.product_category_selfconsumption_pack",
            )
