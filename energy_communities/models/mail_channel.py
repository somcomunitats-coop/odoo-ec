from odoo import models


class Channel(models.Model):
    _inherit = "mail.channel"

    def _subscribe_users_automatically(self):
        new_members = self.sudo()._subscribe_users_automatically_get_members()
        if new_members:
            to_create = [
                {"channel_id": channel_id, "partner_id": partner_id}
                for channel_id in new_members
                for partner_id in new_members[channel_id]
            ]
            self.env["mail.channel.member"].sudo().create(to_create)
