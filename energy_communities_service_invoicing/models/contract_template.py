from odoo import api, fields, models, _

PACK_VALUES = [
    ("platform_pack", _("Platform Pack")),
    ("none", _("None")),
]

class ContractTemplate(models.Model):
    _name = "contract.template"
    _inherit = "contract.template"

    is_free_pack = fields.Boolean(string="Is a free pack")
    pack_type = fields.Selection(PACK_VALUES, compute="_compute_pack_type", string="Pack Type", store=True)
    
    def _get_pack_product_from_category(self, category_id, value):
        return value if bool(
                    self.env["product.template"].search(
                        [
                            ("property_contract_template_id", "=", self.id),
                            (
                                "categ_id",
                                "=",
                                category_id,
                            ),
                        ]
                    )
                ) else 'none'
    
    def _set_custom_pack_type(self, ref_category, value):
        try:
            categ_id = self.env.ref(
                ref_category
            ).id
        except:
            categ_id = False
        if categ_id:
            self.pack_type = self._get_pack_product_from_category(categ_id, value)

    def custom_compute_pack_type(self):
        self._set_custom_pack_type("energy_communities_service_invoicing.product_category_platform_pack", 'platform_pack')

    def _compute_pack_type(self):
        for record in self:
            record.custom_compute_pack_type()

