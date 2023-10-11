from odoo import fields, models


class Contract(models.Model):
    _inherit = "contract.contract"

    project_id = fields.Many2one(
        "energy_project.project",
        ondelete="restrict",
        string="Energy Project",
        check_company=True,
    )
