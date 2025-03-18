from odoo import fields, models

from ..utils import PACK_VALUES


class PackTypeMixin(models.AbstractModel):
    _name = "pack.type.mixin"
    _description = "Add pack_type to any model"

    pack_type = fields.Selection(
        PACK_VALUES,
        compute="_compute_pack_type",
        compute_sudo=True,
        string="Pack Type",
        store=True,
        default="none",
    )

    def _get_pack_type_from_product_category(self, pack_type, category_id):
        return (
            pack_type
            if bool(
                self.env["product.template"].search(
                    [
                        ("property_contract_template_id", "=", self.id),
                        ("categ_id", "=", category_id),
                    ]
                )
            )
            else "none"
        )

    def _set_custom_pack_type_on_contract_template(self, pack_type, ref_category):
        try:
            categ_id = self.env.ref(ref_category).id
        except:
            categ_id = False
        if categ_id:
            self.pack_type = self._get_pack_type_from_product_category(
                pack_type, categ_id
            )

    def _set_custom_pack_type_on_invoice(self):
        if self.ref:
            rel_inv = (
                self.env["account.move"]
                .sudo()
                .search([("name", "=", self.ref)], limit=1)
            )
            if rel_inv:
                self.pack_type = rel_inv.pack_type
        else:
            if self.invoice_line_ids:
                first_move_line = self.invoice_line_ids[0]
                if first_move_line.contract_line_id:
                    rel_contract = first_move_line.contract_line_id.contract_id
                    self.pack_type = rel_contract.pack_type

    # method to be overwriten on implementations
    def custom_compute_pack_type(self):
        pass

    def _compute_pack_type(self):
        for record in self:
            record.pack_type = "none"
            record.custom_compute_pack_type()
