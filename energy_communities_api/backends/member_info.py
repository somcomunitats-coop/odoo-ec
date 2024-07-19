from odoo.api import Environment


class MemberInfoBackend:
    def __init__(self, env: Environment) -> None:
        self.env = env

    def get_member_info(self, partner_id):
        partner = self.env["res.partner"].browse(partner_id)
        return partner.api_member_info()
