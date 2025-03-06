from odoo import api, fields, models, _

PACK_VALUES = [
    ("selfconsumption_pack", _("Selfconsumption Pack")),
]

class ContractTemplate(models.Model):
    _inherit = "contract.template"

    pack_type = fields.Selection(selection_add=PACK_VALUES)

    def custom_compute_pack_type(self):
        super().custom_compute_pack_type()
        if self.pack_type == 'none':
            self.set_custom_pack_type("selfconsumption.product_category_selfconsumption_pack", 'selfconsumption_pack')
