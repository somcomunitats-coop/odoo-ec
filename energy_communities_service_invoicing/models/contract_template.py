from odoo import api, fields, models


class ContractTemplate(models.Model):
    _name = "contract.template"
    _inherit = "contract.template"

    is_pack = fields.Boolean(compute="compute_is_pack", store=True)

    def compute_is_pack(self):
        try:
            categ_id = self.env.ref(
                "energy_communities_service_invoicing.product_category_pack"
            ).id
        except:
            categ_id = False
        if categ_id:
            for record in self:
                record.is_pack = bool(
                    self.env["product.template"].search(
                        [
                            ("property_contract_template_id", "=", record.id),
                            (
                                "categ_id",
                                "=",
                                categ_id,
                            ),
                        ]
                    )
                )
