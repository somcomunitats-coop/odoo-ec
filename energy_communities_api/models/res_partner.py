from odoo import models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "user.currentcompany.mixin"]

    def api_member_info(self):
        self.ensure_one()
        with self.env["member_info.service"].work_on(self._name) as work:
            member_info = work.component(usage="member_info.api").get_member_info(self)
        return member_info
