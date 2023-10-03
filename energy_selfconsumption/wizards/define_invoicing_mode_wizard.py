from odoo import _, fields, models


class ContractGenerationWizard(models.TransientModel):
    _name = "energy_selfconsumption.define_invoicing_mode.wizard"

    INVOICING_VALUES = [
        ("power_acquired", _("By power acquired")),
        ("energy_delivered", _("By energy delivered")),
        (
            "energy_delivered_hourly",
            _("For energy delivered hourly variable coefficients (CSV)"),
        ),
    ]

    invoicing_mode = fields.Selection(
        INVOICING_VALUES,
        string=_("Invoicing Mode"),
        default="power_acquired",
        required=True,
    )
