from odoo import _, api, fields, models


class SupplyPoint(models.Model):
    _name = "energy_selfconsumption.supply_point"
    _description = "Energy Supply Point"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    _sql_constraints = {
        (
            "unique_code_company_id",
            "unique (code, company_id)",
            _("A supply point with this code already exists."),
        )
    }

    name = fields.Char(compute="_compute_supply_point_name", store=True)
    code = fields.Char(string="CUPS", required=True)
    owner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
        help="Partner with the legal obligation of the supply point",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Cooperator",
        required=True,
        help="Cooperator subscribed to the self-consumption project",
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, readonly=True
    )
    reseller_id = fields.Many2one(
        "energy_project.reseller", string="Reseller", domain=[("state", "!=", "Baja")]
    )

    # Address fields
    street = fields.Char(required=True)
    street2 = fields.Char(required=True)
    zip = fields.Char(change_default=True, required=True)
    city = fields.Char(required=True)
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
        ondelete="restrict",
        domain="[('country_id', '=?', country_id)]",
        required=True,
    )
    country_id = fields.Many2one(
        "res.country", string="Country", ondelete="restrict", required=True
    )

    supply_point_assignation_ids = fields.One2many(
        "energy_selfconsumption.supply_point_assignation",
        "supply_point_id",
        readonly=True,
    )
    supplier_id = fields.Many2one("energy_project.supplier", string="Supplier")

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        self.owner_id = self.partner_id

    @api.depends("partner_id", "street")
    def _compute_supply_point_name(self):
        for record in self:
            if record.partner_id and record.street:
                record.name = f"{record.partner_id.name} - {record.street}"
            else:
                record.name = _("New Supply Point")
