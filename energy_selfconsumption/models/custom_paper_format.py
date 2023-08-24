from odoo import models, fields

class CustomPaperFormat(models.Model):
    _inherit = 'report.paperformat'

    custom_format_name = fields.Char('Custom Format Name', required=True)
    custom_page_width = fields.Float('Custom Page Width')
    custom_page_height = fields.Float('Custom Page Height')
    custom_margin_top = fields.Float('Custom Margin Top')
    custom_margin_bottom = fields.Float('Custom Margin Bottom')
    custom_margin_left = fields.Float('Custom Margin Left')
    custom_margin_right = fields.Float('Custom Margin Right')
    orientation = fields.Char('Orientation')