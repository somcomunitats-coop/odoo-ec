from odoo import fields, models


class ProjectType(models.Model):
    _name = "energy_project.project_type"
    _description = "Type for energy project"

    name = fields.Char(required=True)
