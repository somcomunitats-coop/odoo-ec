from odoo import _, api, fields, models
from odoo.exceptions import UserError


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

    def unlink(self):
        related_projects = []
        to_delete_assignations = self.env['energy_selfconsumption.supply_point_assignation']
        for inscription in self:
            related_tables = self.env['energy_selfconsumption.distribution_table'].search([
                ('state', 'in', ['validated', 'process', 'active']),
                ('selfconsumption_project_id', '=', inscription.project_id.id)
            ])
            if related_tables:
                related_projects.append(inscription.project_id.name)
            else:
                partner_assignations = self.env['energy_selfconsumption.supply_point_assignation'].search([
                    ('distribution_table_id.selfconsumption_project_id.inscription_ids.partner_id', '=', inscription.partner_id.id),
                    ('selfconsumption_project_id', '=', inscription.project_id.id),
                ])
                to_delete_assignations |= partner_assignations
        if related_projects:
            project_names = ', '.join(related_projects)
            raise UserError(_(
                "Cannot delete inscription. It is related to the following project(s): %s" % project_names
            ))
        if to_delete_assignations:
            to_delete_assignations.unlink()

        return super(Inscription, self).unlink()
