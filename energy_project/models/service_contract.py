from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ServiceContract(models.Model):
    _name = "energy_project.service_contract"
    _description = "Energy Services Contract"

    _sql_constraints = {
        (
            "unique_service_id_provider_id_project_id",
            "unique (service_id, provider_id, project_id)",
            _("There's already a service with this provider assigned to this project."),
        )
    }

    @api.depends("service_id")
    def _compute_available_providers_ids(self):
        for service_contract in self:
            service_contract.available_providers_ids = (
                service_contract.service_id.service_available_ids.mapped(
                    "provider_id"
                ).ids
            )

    service_id = fields.Many2one(
        "energy_project.service", string="Service", required=True
    )
    provider_id = fields.Many2one(
        "energy_project.provider", string="Provider", required=True
    )
    available_providers_ids = fields.Many2many(
        "energy_project.provider",
        compute=_compute_available_providers_ids,
        string="Available Providers",
    )
    project_id = fields.Many2one(
        "energy_project.project", required=True, ondelete="cascade"
    )
    active = fields.Boolean(string="Active", required=True, default=True)

    @api.onchange("service_id")
    def _onchange_service_id(self):
        if self._provider_is_available():
            self.provider_id = False

    @api.constrains("provider_id")
    def _check_provider_id(self):
        for record in self:
            if record._provider_is_available():
                raise ValidationError(
                    _(
                        "The {provider_name} provider doesn't provide this {service_name} service."
                    ).format(
                        **{
                            "provider_name": record.provider_id.name,
                            "service_name": record.service_id.name,
                        }
                    )
                )

    def _provider_is_available(self):
        self.ensure_one()
        return self.provider_id.id not in self.available_providers_ids.ids
