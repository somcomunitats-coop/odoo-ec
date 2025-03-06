from odoo import api, fields, models


class ContractTemplate(models.Model):
    _name = "contract.template"
    _inherit = "contract.template"

    is_pack = fields.Boolean(compute="compute_is_pack", store=True)
    is_free_pack = fields.Boolean(string="Is a free pack")

    def compute_is_pack(self):
        try:
            categ_id = self.env.ref(
                "energy_communities_service_invoicing.product_category_pack"
            ).id
        except:
            categ_id = False
        for record in self:
            if categ_id:
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
