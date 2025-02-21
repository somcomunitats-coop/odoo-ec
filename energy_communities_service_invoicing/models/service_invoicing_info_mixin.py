from odoo import api, fields, models


class ServiceInvoicingInfoMixin(models.AbstractModel):
    _name = "service.invoicing.info.mixin"
    _description = "Get info about current service invoicing configuration"

    pack_product_product_ids = fields.Many2many(
        comodel_name="product.product",
        _compute="_compute_pack_product_product_ids",
        store=False,
    )

    @api.depends("name")
    def _compute_pack_product_product_ids(self):
        for record in self:
            pack_product_product_ids = []
            record.pack_product_product_ids = self.env["product.product"].search(
                [
                    (
                        "categ_id",
                        "=",
                        self.env.ref(
                            "energy_communities_service_invoicing.product_category_pack"
                        ).id,
                    )
                ]
            )
