from stdnum.es import cups, referenciacatastral
from stdnum.eu import vat
from stdnum.exceptions import *

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

    _ACCESS_TARIFF_VALUES = [
        ("2.0TD", "2.0TD"),
        ("3.0TD", "3.0TD"),
        ("6.1TD", "6.1TD"),
        ("6.2TD", "6.2TD"),
        ("6.3TD", "6.3TD"),
        ("6.4TD", "6.4TD"),
    ]

    name = fields.Char(compute="_compute_supply_point_name", store=True)
    code = fields.Char(string="CUPS")
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
    cadastral_reference = fields.Char(string="Cadastral reference")
    contracted_power = fields.Float(
        string="Contracted power", digits=(10, 6), help="Value in kilowatts (kW)"
    )
    tariff = fields.Selection(_ACCESS_TARIFF_VALUES, "Access tariff")

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

    @api.constrains("code")
    def _check_valid_code(self):
        for record in self:
            if record.code:
                try:
                    cups.validate(record.code)
                except InvalidLength:
                    error_message = _("Invalid CUPS: The length is incorrect.")
                    raise ValidationError(error_message)
                except InvalidComponent:
                    error_message = _("Invalid CUPS: does not start with 'ES'.")
                    raise ValidationError(error_message)
                except InvalidFormat:
                    error_message = _("Invalid CUPS: has an incorrect format.")
                    raise ValidationError(error_message)
                except InvalidChecksum:
                    error_message = _("Invalid CUPS: The checksum is incorrect.")
                    raise ValidationError(error_message)

    @api.constrains("cadastral_reference")
    def _check_valid_cadastral_reference(self):
        for record in self:
            if record.cadastral_reference:
                try:
                    referenciacatastral.validate(self.cadastral_reference)
                except Exception as e:
                    error_message = _("Invalid Cadastral Reference: {error}").format(
                        error=e
                    )
                    raise ValidationError(error_message)

    @api.constrains("owner_id")
    def _check_valid_vat(self):
        for record in self:
            original_vat = record.owner_id.vat
            if original_vat:
                if not original_vat.startswith("ES"):
                    original_vat = "ES" + original_vat
                try:
                    vat.validate(original_vat)
                except Exception as e:
                    error_message = _("Invalid VAT: {error}").format(error=e)
                    raise ValidationError(error_message)

    @api.constrains("tariff", "contracted_power")
    def _check_contracted_power(self):
        for record in self:
            if record.tariff == "2.0TD" and not (0 <= record.contracted_power <= 15):
                raise ValidationError(
                    "For the 2.0TD rate, the contracted power must be between 0 and 15 kW."
                )
            elif record.tariff == "3.0TD" and record.contracted_power <= 15:
                raise ValidationError(
                    "For the 3.0TD rate, the contracted power must be greater than 15 kW."
                )

            if record.contracted_power > 100:
                message = _(
                    "The indicated contracted power is very high. Please check that this is correct. Remember that we use '.' to express decimals, not ','."
                )
                record.message_post(body=message, subtype_xmlid="mail.mt_comment")
