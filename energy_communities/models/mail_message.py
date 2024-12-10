from odoo import api, models


class Message(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, values_list):
        return super(Message, self.sudo()).create(values_list)
