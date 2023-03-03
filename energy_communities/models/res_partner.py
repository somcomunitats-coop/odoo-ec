from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    gender = fields.Selection(selection_add=[("not_binary", "Not binary"),
                                             ("not_share", "I prefer to not share it")])

    def get_cooperator_from_vat(self, vat):
        if vat:
            vat = vat.strip()
        # email could be falsy or be only made of whitespace.
        if not vat:
            return self.browse()
        partner = self.search(
            [("vat", "ilike", vat)], limit=1
        )
        return partner
