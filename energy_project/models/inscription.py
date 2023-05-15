from odoo import _, fields, models


class Inscription(models.Model):
    _name = "energy_project.inscription"
    _description = "Inscriptions for a project"

    _sql_constraints = {
        (
            "unique_project_id_partner_id",
            "unique (project_id, partner_id)",
            _("Partner is already signed up in this project."),
        )
    }

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, readonly=True
    )
    project_id = fields.Many2one(
        "energy_project.project",
        required=True,
        ondelete="restrict",
        string="Energy Project",
        check_company=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        ondelete="restrict",
        string="Partner",
    )
    effective_date = fields.Date(required=True)
