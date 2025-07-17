from datetime import datetime

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import (
    contract_utils,
    get_successful_popup_message,
    sale_order_utils,
)


class AssignPackToPartnerWizard(models.TransientModel):
    _name = "assign.pack.to.partner.wizard"
    _description = "Assistant for assigning a pack to a set of partners"

    activation_date = fields.Date(string="Activation date", default=datetime.now())
    pack_id = fields.Many2one(
        "product.template",
        string="Pack",
        domain="[('is_assignable_pack_to_partner','=',True),('company_id','in',allowed_company_ids)]",
    )
    payment_mode_id = fields.Many2one(
        "account.payment.mode",
        string="Payment mode",
        domain="[('company_id', 'in', allowed_company_ids)]",
    )
    partner_mids = fields.Many2many(
        "res.partner",
        "res_partner_pack_assignation_wizard_rel",
        "assign_pack_to_partner_wizard_id",
        "partner_id",
        string="Partners to apply",
        domain="[('company_id','!=',False)]",
    )
    allowed_company_ids = fields.Many2many(
        comodel_name="res.company",
        compute="_compute_allowed_company_ids",
        store=False,
    )

    def _compute_allowed_company_ids(self):
        for record in self:
            record.allowed_company_ids = self.env["res.company"].search(
                [("id", "=", self.env.company.id)]
            )

    def execute_assignation(self):
        self._validate_assignation()
        self._assign_pack()
        return get_successful_popup_message(
            _("Pack assignation successful"),
            _("Please visit impacted partners view in order to see new contracts."),
        )

    def _validate_assignation(self):
        if not self.partner_mids:
            raise ValidationError(_("Please select at least one partner"))
        if not self.pack_id.company_id.pricelist_id:
            raise ValidationError(
                _("You must configure company's tariffs before executing this action")
            )

    def _assign_pack(self):
        created_contracts = []
        with sale_order_utils(self.env) as component:
            for partner in self.partner_mids:
                if self.pack_id.company_id:
                    so_metadata = {"company_id": self.pack_id.company_id.id}
                else:
                    so_metadata = {"company_id": self.env.ref("base.main_company").id}
                created_contracts.append(
                    component.create_service_invoicing_initial(
                        partner,
                        self.pack_id,
                        self.pack_id.company_id.pricelist_id,
                        self.activation_date,
                        "activate",
                        "assign_pack_to_partner",
                        self.payment_mode_id,
                        so_metadata,
                    )
                )
        for contract in created_contracts:
            with contract_utils(self.env, contract) as component:
                component.activate(self.activation_date)
        return created_contracts
