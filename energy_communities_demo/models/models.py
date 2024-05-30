# from odoo import models, fields, api


# class energy_communities_demo(models.Model):
#     _name = 'energy_communities_demo.energy_communities_demo'
#     _description = 'energy_communities_demo.energy_communities_demo'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
