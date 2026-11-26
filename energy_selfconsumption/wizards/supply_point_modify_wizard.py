from markupsafe import Markup

from odoo import _, api, fields, models


class SupplyPointModifyWizard(models.TransientModel):
    """Change the cooperator or the owner of an existing supply point.

    CUPS stays untouched. The owner is not replaced when the cooperator
    changes. Each real change, and an optional justification, is posted
    on the supply point chatter with a link to the partners involved.
    """

    _name = "energy_selfconsumption.supply_point.modify.wizard"
    _description = "Modify Supply Point"

    supply_point_id = fields.Many2one(
        "energy_selfconsumption.supply_point",
        required=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Cooperator",
        required=True,
    )
    owner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
    )
    original_partner_id = fields.Many2one(
        "res.partner",
        readonly=True,
    )
    original_owner_id = fields.Many2one(
        "res.partner",
        readonly=True,
    )
    justification = fields.Text(string="Change justification")
    show_partner_warning = fields.Boolean(
        compute="_compute_change_warnings",
    )
    show_owner_warning = fields.Boolean(
        compute="_compute_change_warnings",
    )

    @api.depends(
        "partner_id",
        "owner_id",
        "original_partner_id",
        "original_owner_id",
    )
    def _compute_change_warnings(self):
        for wizard in self:
            wizard.show_partner_warning = (
                wizard.partner_id != wizard.original_partner_id
            )
            wizard.show_owner_warning = wizard.owner_id != wizard.original_owner_id

    def action_confirm(self):
        """Apply the cooperator and owner changes and log them."""
        self.ensure_one()
        supply_point = self.supply_point_id
        values = {}
        if self.partner_id != self.original_partner_id:
            values["partner_id"] = self.partner_id.id
        if self.owner_id != self.original_owner_id:
            values["owner_id"] = self.owner_id.id
        if values:
            supply_point.write(values)
        if "partner_id" in values:
            supply_point.message_post(
                body=self._cooperator_change_message(),
                subtype_xmlid="mail.mt_note",
            )
        if "owner_id" in values:
            supply_point.message_post(
                body=self._owner_change_message(),
                subtype_xmlid="mail.mt_note",
            )
        if (self.justification or "").strip():
            supply_point.message_post(
                body=self._justification_message(),
                subtype_xmlid="mail.mt_note",
            )
        return {"type": "ir.actions.act_window_close"}

    def _partner_link(self, partner):
        title = "[{}] {}".format(partner.id, partner.display_name)
        return partner._get_html_link(title=title)

    def _cooperator_change_message(self):
        return Markup(
            _(
                "COOPERATOR CHANGE: User %(user)s has changed the existing "
                "cooperator %(old)s for this new one %(new)s"
            )
        ) % {
            "user": self.env.user.name,
            "old": self._partner_link(self.original_partner_id),
            "new": self._partner_link(self.partner_id),
        }

    def _owner_change_message(self):
        return Markup(
            _(
                "OWNER CHANGE: User %(user)s has changed the existing owner "
                "%(old)s for this new one %(new)s"
            )
        ) % {
            "user": self.env.user.name,
            "old": self._partner_link(self.original_owner_id),
            "new": self._partner_link(self.owner_id),
        }

    def _justification_message(self):
        return Markup(_("CHANGE JUSTIFICATION: %(justification)s")) % {
            "justification": self.justification.strip(),
        }
