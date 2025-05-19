import base64
import logging
from datetime import datetime, timedelta
from io import StringIO

import chardet
import pandas as pd
from stdnum.es import cups, referenciacatastral
from stdnum.exceptions import *

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.energy_communities.utils import (
    contract_utils,
    sale_order_utils,
)
from odoo.addons.energy_communities_service_invoicing.utils import (
    get_existing_pack_contract,
)

_logger = logging.getLogger(__name__)


INVOICING_VALUES = [
    ("power_acquired", _("Power Acquired")),
    ("energy_delivered", _("Energy Delivered")),
    ("energy_custom", _("Energy Delivered Custom")),
]

ACTIVE = "active"
INACTIVE = "inactive"

CONF_STATE_VALUES = [
    (ACTIVE, _("Active")),
    (INACTIVE, _("Inactive")),
]


class Selfconsumption(models.Model):
    _name = "energy_selfconsumption.selfconsumption"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {
        "energy_project.project": "project_id",
    }
    _description = "Self-consumption Energy Project"

    _sql_constraints = [
        (
            "unique_code",
            "UNIQUE(code)",
            _("A project with this CAU already exists."),
        ),
    ]

    def _compute_distribution_table_count(self):
        for record in self:
            record.distribution_table_count = len(record.distribution_table_ids)

    def _compute_inscription_count(self):
        for record in self:
            record.inscription_count = len(record.inscription_ids)

    def _compute_contract_count(self):
        for record in self:
            related_contracts = self.env["contract.contract"].search_count(
                [("project_id", "=", record.id), ("status", "=", "in_progress")]
            )
            record.contracts_count = related_contracts

    def _compute_sale_orders_count(self):
        for record in self:
            sale_orders = self.get_sale_orders()
            record.sale_orders_count = len(sale_orders)

    def _compute_report_distribution_table(self):
        """
        This compute field gets the distribution table needed to generate the reports.
        It prioritizes the table in process and then the active one. It can only be one of each.
        """
        for record in self:
            table_in_process = record.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            )
            table_in_active = record.distribution_table_ids.filtered_domain(
                [("state", "=", ACTIVE)]
            )
            if table_in_process:
                record.report_distribution_table = table_in_process
            elif table_in_active:
                record.report_distribution_table = table_in_active
            else:
                record.report_distribution_table = False

    def _compute_current_distribution_table(self):
        for record in self:
            table_in_active = record.distribution_table_ids.filtered_domain(
                [("state", "=", "active")]
            )
            if table_in_active:
                record.current_distribution_table = table_in_active
            else:
                record.current_distribution_table = False

    project_id = fields.Many2one(
        "energy_project.project", required=True, ondelete="cascade"
    )
    code = fields.Char(string="CAU")
    cil = fields.Char(
        string="CIL", help="Production facility code for liquidation purposes"
    )
    owner_id = fields.Many2one(
        "res.partner",
        string="Owner",
        required=True,
        default=lambda self: self.env.company.partner_id,
    )
    power = fields.Float(string="Power (kW)")
    distribution_table_ids = fields.One2many(
        "energy_selfconsumption.distribution_table",
        "selfconsumption_project_id",
        readonly=True,
    )
    report_distribution_table = fields.Many2one(
        "energy_selfconsumption.distribution_table",
        compute=_compute_report_distribution_table,
        readonly=True,
    )
    current_distribution_table = fields.Many2one(
        "energy_selfconsumption.distribution_table",
        compute=_compute_current_distribution_table,
        readonly=True,
        store=False,
    )
    distribution_table_count = fields.Integer(compute=_compute_distribution_table_count)
    inscription_ids = fields.One2many(
        "energy_selfconsumption.inscription_selfconsumption",
        "selfconsumption_project_id",
        readonly=True,
    )
    inscription_count = fields.Integer(compute=_compute_inscription_count)
    contracts_count = fields.Integer(compute=_compute_contract_count)
    sale_orders_count = fields.Integer(compute=_compute_sale_orders_count)
    invoicing_mode = fields.Selection(INVOICING_VALUES, string="Invoicing Mode")
    payment_mode_id = fields.Many2one("account.payment.mode", string="Payment mode")
    product_id = fields.Many2one("product.product", string="Product")
    contract_template_id = fields.Many2one(
        "contract.template",
        string="Contract Template",
        related="product_id.property_contract_template_id",
    )
    supplier_id = fields.Many2one(
        "energy_project.supplier",
        string="Energy Supplier",
        help="Select the associated Energy Supplier",
    )
    cadastral_reference = fields.Char(string="Cadastral reference")
    conf_state = fields.Selection(
        CONF_STATE_VALUES,
        string="Activate Registration Form",
        default=INACTIVE,
        required=True,
    )
    conf_participation_ids = fields.One2many(
        "energy_selfconsumptions.participation",
        "project_id",
        string="Participation",
    )
    conf_used_in_selfconsumption = fields.Boolean("Show used in selfconsumption")
    conf_vulnerability_situation = fields.Boolean("Show vulnerability situation")
    conf_bank_details = fields.Boolean(
        "Request bank details",
        default=True,
        help="Select when you want to make the payment by bank transfer. If not requested, the payment must be made by bank transfer by the member.",
    )
    conf_url_form = fields.Char(string="URL")

    @api.constrains("code")
    def _check_valid_code(self):
        """
        The following are evaluated:
            1. The first 20 or 22 digits correspond to the CUPS.
            2. The character after CUPS is A
            3. And the last 3 characters are numbers.
            4. Taking into account that the length of the CUPS can vary, the length of the CAU can be 24 or 26 characters.
        """
        for record in self:
            if record.code:
                # Validate the total length of the CAU, check if the first digits are CUPS and get the last 4 characters
                if len(record.code) == 24:
                    try:
                        cups.validate(record.code[:20])
                    except InvalidLength:
                        error_message = _(
                            "Invalid CAU: The first characters related to CUPS are incorrect. The length is incorrect."
                        )
                        raise ValidationError(error_message)
                    except InvalidComponent:
                        error_message = _(
                            "Invalid CAU: The CUPS does not start with 'ES'."
                        )
                        raise ValidationError(error_message)
                    except InvalidFormat:
                        error_message = _(
                            "Invalid CAU: The CUPS has an incorrect format."
                        )
                        raise ValidationError(error_message)
                    except InvalidChecksum:
                        error_message = _(
                            "Invalid CAU: The checksum of the CUPS is incorrect."
                        )
                        raise ValidationError(error_message)
                    last_digits = record.code[20:]
                elif len(record.code) == 26:
                    try:
                        cups.validate(record.code[:22])
                    except InvalidLength:
                        error_message = _(
                            "Invalid CAU: The first characters related to CUPS are incorrect. The length is incorrect."
                        )
                        raise ValidationError(error_message)
                    except InvalidComponent:
                        error_message = _(
                            "Invalid CAU: The CUPS does not start with 'ES'."
                        )
                        raise ValidationError(error_message)
                    except InvalidFormat:
                        error_message = _(
                            "Invalid CAU: The CUPS has an incorrect format."
                        )
                        raise ValidationError(error_message)
                    except InvalidChecksum:
                        error_message = _(
                            "Invalid CAU: The checksum of the CUPS is incorrect."
                        )
                        raise ValidationError(error_message)
                    last_digits = record.code[22:]
                else:
                    error_message = _("Invalid CAU: The length is not correct")
                    raise ValidationError(error_message)

                # Check if the character after CUPS is 'A'
                if not last_digits.startswith("A"):
                    error_message = _("Invalid CAU: The character after CUPS is not A")
                    raise ValidationError(error_message)

                # Check if the last 3 characters are numbers
                if not last_digits[-3:].isdigit():
                    error_message = _("Invalid CAU: Last 3 digits are not numbers")
                    raise ValidationError(error_message)

    @api.constrains("cil")
    def _check_valid_cil(self):
        """
        The following are evaluated:
            1. The first 20 or 22 digits correspond to the CUPS.
            2. And the last 3 characters are numbers.
        """
        for record in self:
            if record.cil:
                if len(record.cil) == 23:
                    try:
                        cups.validate(record.code[:20])
                    except InvalidLength:
                        error_message = _(
                            "Invalid CIL: The first characters related to CUPS are incorrect. The length is incorrect."
                        )
                        raise ValidationError(error_message)
                    except InvalidComponent:
                        error_message = _(
                            "Invalid CIL: The CUPS does not start with 'ES'."
                        )
                        raise ValidationError(error_message)
                    except InvalidFormat:
                        error_message = _(
                            "Invalid CIL: The CUPS has an incorrect format."
                        )
                        raise ValidationError(error_message)
                    except InvalidChecksum:
                        error_message = _(
                            "Invalid CIL: The checksum of the CUPS is incorrect."
                        )
                        raise ValidationError(error_message)
                    last_digits = record.cil[20:]
                elif len(record.cil) == 25:
                    try:
                        cups.validate(record.code[:22])
                    except InvalidLength:
                        error_message = _(
                            "Invalid CIL: The first characters related to CUPS are incorrect. The length is incorrect."
                        )
                        raise ValidationError(error_message)
                    except InvalidComponent:
                        error_message = _(
                            "Invalid CIL: The CUPS does not start with 'ES'."
                        )
                        raise ValidationError(error_message)
                    except InvalidFormat:
                        error_message = _(
                            "Invalid CIL: The CUPS has an incorrect format."
                        )
                        raise ValidationError(error_message)
                    except InvalidChecksum:
                        error_message = _(
                            "Invalid CIL: The checksum of the CUPS is incorrect."
                        )
                        raise ValidationError(error_message)
                    last_digits = record.cil[22:]
                else:
                    error_message = _("Invalid CIL: The length is not correct")
                    raise ValidationError(error_message)

                # Check if the last 3 characters are numbers
                if not last_digits[-3:].isdigit():
                    error_message = _("Invalid CIL: Last 3 digits are not numbers")
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

    @api.model_create_multi
    def create(self, values):
        res = super().create(values)
        self.env["energy_selfconsumptions.participation"].create(
            {
                "name": "0,5 kW",
                "quantity": 0.5,
                "project_id": res.id,
            }
        )
        self.env["energy_selfconsumptions.participation"].create(
            {
                "name": "1,0 kW",
                "quantity": 1.0,
                "project_id": res.id,
            }
        )
        self.env["energy_selfconsumptions.participation"].create(
            {
                "name": "1,5 kW",
                "quantity": 1.5,
                "project_id": res.id,
            }
        )
        self.env["energy_selfconsumptions.participation"].create(
            {
                "name": "2,0 kW",
                "quantity": 2.0,
                "project_id": res.id,
            }
        )
        return res

    def unlink(self):
        for record in self:
            # TODO:
            # An extra control is needed when deleting a supply_point_assignation_ids
            # depending on the state of the distribution_table_ids model.
            # record.distribution_table_ids.supply_point_assignation_ids.unlink()
            # Extra control is needed when deleting a distribution_table_ids
            # depending on the status
            # record.distribution_table_ids.unlink()
            # An extra control is needed when deleting an inscription_ids depending
            # on whether the supply_point_assignation_ids model of
            # distribution_table_ids is present. And depending on whether it is an open
            # enrollment for the public.
            # record.inscription_ids.unlink()
            record.project_id.unlink()
        return super().unlink()

    def set_inscription(self):
        for record in self:
            record.write({"state": "inscription"})

    def set_inscription_activation(self):
        self.set_inscription()
        self.distribution_table_state("process", "validated")

    def set_draft(self):
        for record in self:
            record.write({"state": "draft"})

    def set_invoicing_mode(self):
        return {
            "name": _("Define Invoicing Mode"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "energy_selfconsumption.define_invoicing_mode.wizard",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": {"default_selfconsumption_id": self.id},
        }

    def set_new_distribution_table(self):
        distribution_table_active = self.distribution_table_ids.filtered(
            lambda table: table.state == ACTIVE
        )
        if not distribution_table_active:
            raise ValidationError(_("There is no active distribution table."))
        distribution_table_validated = self.distribution_table_ids.filtered(
            lambda table: table.state == "validated"
        )
        if not distribution_table_validated:
            raise ValidationError(_("There is no validated distribution table."))

        self.distribution_table_state("validated", ACTIVE)

        # TODO:
        # Generate new sale orders
        # Select product
        pack = None
        if self.invoicing_mode == "power_acquired":
            pack = self.env.ref(
                "energy_selfconsumption.product_product_power_acquired_product_pack_template"
            )
        elif self.invoicing_mode == "energy_delivered":
            pack = self.env.ref(
                "energy_selfconsumption.product_product_energy_delivered_product_pack_template"
            )
        elif self.invoicing_mode == "energy_custom":
            pack = self.env.ref(
                "energy_selfconsumption.product_product_energy_custom_product_pack_template"
            )
        else:
            raise ValidationError(_("Invalid invoicing mode"))

        # Create sale order
        for (
            supply_point_assignation
        ) in distribution_table_validated.supply_point_assignation_ids:
            inscription_id = self.selfconsumption_id.inscription_ids.filtered_domain(
                [
                    (
                        "partner_id",
                        "=",
                        supply_point_assignation.supply_point_id.partner_id.id,
                    )
                ]
            )
            if not inscription_id.mandate_id:
                raise ValidationError(
                    _("Mandate not found for {partner}").format(
                        partner=supply_point_assignation.supply_point_id.partner_id.name
                    )
                )

            service_invoicing_id = False
            existing_contract = get_existing_pack_contract(
                self.env,
                inscription_id.partner_id,
                "selfconsumption_pack",
                ["closed_planned", "in_progress", "paused", "closed"],
                [("project_id", "=", self.id)],
            )
            if not existing_contract:
                so_metadata = {
                    "selfconsumption_id": self.id,
                    "supply_point_id": supply_point_assignation.supply_point_id.id,
                    "recurring_interval": self.recurring_interval,
                    "recurring_rule_type": self.recurring_rule_type,
                    "recurring_invoicing_type": self.recurring_invoicing_type,
                    "project_id": self.id,
                    "company_id": self.company_id.id,
                }
                # config journal if defined
                sale_journal_id = pack.categ_id.with_context(
                    company_id=self.company_id.id
                ).service_invoicing_sale_journal_id
                if sale_journal_id:
                    so_metadata["journal_id"] = sale_journal_id.id
                # create service invoicing
                with sale_order_utils(self.env) as component:
                    service_invoicing_id = component.create_service_invoicing_initial(
                        inscription_id.partner_id,
                        pack,
                        self.pricelist_id,
                        fields.Date.today(),
                        "activate",
                        "active_selfconsumption_contract",
                        self.payment_mode_id,
                        so_metadata,
                    )
            if not service_invoicing_id:
                existing_closed_contract = get_existing_pack_contract(
                    self.env,
                    inscription_id.partner_id,
                    "selfconsumption_pack",
                    ["closed_planned", "closed"],
                    [("project_id", "=", self.id)],
                )
                if existing_closed_contract:
                    with contract_utils(
                        self.env, existing_closed_contract
                    ) as component:
                        service_invoicing_id = component.reopen(
                            fields.Date.today(),
                            self.pricelist_id,
                            pack,
                            False,
                            self.payment_mode_id,
                        )
            if service_invoicing_id:
                # 2.- setup contract line description
                self._setup_selfconsumption_contract_line_description(
                    distribution_table_validated, service_invoicing_id
                )
                # 3.- setup contract line main_line
                service_invoicing_id.contract_line_ids[0].write({"main_line": True})
                # 4.- mark contract as active
                with contract_utils(self.env, service_invoicing_id) as component:
                    component.set_contract_status_active(fields.Date.today())

    def set_in_activation_state(self):
        for record in self:
            if not record.code:
                raise ValidationError(_("Project must have a valid Code."))
            if not record.power or record.power <= 0:
                raise ValidationError(_("Project must have a valid Rated Power."))
            if not record.distribution_table_ids.filtered_domain(
                [("state", "=", "validated")]
            ):
                raise ValidationError(_("Must have a valid Distribution Table."))
            record.write({"state": "activation"})
        self.distribution_table_state("validated", "process")

    def activate(self):
        """
        Activates the energy self-consumption project, performing various validations.

        This method checks for the presence of a valid code, and rated power
        for the project. If all validations pass, it instances a wizard and generating
        contracts for the project.

        Note:
            The change of state for the 'self-consumption' and 'distribution_table'
            models is performed in the wizard that gets opened. These state changes
            are executed only after the contracts have been successfully generated.

        Returns:
            dict: A dictionary containing the action details for opening the wizard.

        Raises:
            ValidationError: If the project does not have a valid Code, or Rated Power.
        """
        for record in self:
            if not record.code:
                raise ValidationError(_("Project must have a valid Code."))
            if not record.power or record.power <= 0:
                raise ValidationError(_("Project must have a valid Rated Power."))
            if not record.invoicing_mode:
                raise ValidationError(
                    _("Project must have defined a invoicing mode before activation.")
                )
            return {
                "name": _("Generate Contracts"),
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "energy_selfconsumption.contract_generation.wizard",
                "views": [(False, "form")],
                "view_id": False,
                "target": "new",
                "context": {
                    "default_selfconsumption_id": self.id,
                    "default_company_id": self.env.company.id,
                },
            }

    def activate_form(self):
        self.ensure_one()  # Ensures only one record is selected
        if self.conf_state != ACTIVE:
            if not self.company_id.data_policy_approval_text:
                raise ValidationError(
                    _(
                        "You need to add the privacy policy file to display the form."
                        "To modify the privacy policy go to company settings."
                    )
                )
            self.conf_state = ACTIVE
            self.conf_url_form = (
                "{base_url}/inscription-data?model_id={model_id}".format(
                    base_url=self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("web.base.url"),
                    model_id=self._origin.id,
                )
            )

    def unactivate_form(self):
        self.ensure_one()  # Ensures only one record is selected
        if self.conf_state == ACTIVE:
            self.conf_url_form = ""
            self.conf_state = INACTIVE

    def action_redirect_to_page_form_inscription(self):
        self.ensure_one()  # Ensures only one record is selected
        return {
            "type": "ir.actions.act_url",
            "url": self.conf_url_form,
            "target": "new",
        }

    def get_distribution_tables_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Distribution Tables",
            "view_mode": "tree,form",
            "res_model": "energy_selfconsumption.distribution_table",
            "domain": [("selfconsumption_project_id", "=", self.id)],
            "context": {"create": True, "default_selfconsumption_project_id": self.id},
        }

    def get_inscriptions_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Inscriptions",
            "view_mode": "tree,form",
            "res_model": "energy_selfconsumption.inscription_selfconsumption",
            "domain": [
                ("project_id", "=", self.project_id.id),
                ("selfconsumption_project_id", "=", self.id),
            ],
            "context": {
                "create": True,
                "default_project_id": self.project_id.id,
                "default_selfconsumption_project_id": self.id,
            },
        }

    def get_sale_orders(self):
        return (
            self.env["sale.order.metadata.line"]
            .search([("key", "=", "selfconsumption_id"), ("value", "=", str(self.id))])
            .mapped("order_id")
        )

    def get_sale_orders_view(self):
        self.ensure_one()
        sale_orders = self.get_sale_orders()
        return {
            "type": "ir.actions.act_window",
            "name": "Sale Orders",
            "view_mode": "tree,form",
            "res_model": "sale.order",
            "domain": [("id", "in", sale_orders.ids)],
        }

    # TODO: Review if we need to use all contracts or only the active ones when this method is used
    def get_contracts(self):
        return self.env["contract.contract"].search([("project_id", "=", self.id)])

    def get_contracts_view(self):
        self.ensure_one()
        contracts = self.get_contracts()
        return {
            "type": "ir.actions.act_window",
            "name": "Contracts",
            "view_type": "tree",
            "view_mode": "tree,form",
            "views": [
                (
                    self.env.ref(
                        "energy_communities_service_invoicing.view_service_invoicing_tree"
                    ).id,
                    "tree",
                ),
                (
                    self.env.ref(
                        "energy_communities_service_invoicing.view_contract_contract_customer_form_platform_admin"
                    ).id,
                    "form",
                ),
            ],
            "res_model": "contract.contract",
            "domain": [("id", "in", contracts.ids)],
            "context": {
                "create": True,
                "default_project_id": self.id,
                "search_default_not_finished": 1,
                "search_default_paused": 1,
            },
            "target": "current",
        }

    def distribution_table_state(self, actual_state, new_state):
        distribution_table_to_activate = self.distribution_table_ids.filtered(
            lambda table: table.state == actual_state
        )
        # If the new state is active, we need to cancel the active distribution table
        if new_state == ACTIVE:
            distribution_table_active = self.distribution_table_ids.filtered(
                lambda table: table.state == ACTIVE
            )
            if distribution_table_active:
                distribution_table_active.write(
                    {"date_end": fields.Date.today(), "state": "cancelled"}
                )
        distribution_table_to_activate.write({"state": new_state})
        if new_state == ACTIVE:
            # We need to update the start date of the distribution table
            distribution_table_to_activate.write({"date_start": fields.Date.today()})
            # If the new state is active, we need to update the inscriptions
            for supply_point_assignation in distribution_table_to_activate.mapped(
                "supply_point_assignation_ids"
            ):
                inscription = supply_point_assignation._get_inscription()
                inscription.write(
                    {
                        "participation_real_quantity": supply_point_assignation.energy_shares,
                        "state": ACTIVE,
                    }
                )
            inscriptions = self.inscription_ids.filtered_domain(
                [("state", "=", "change")]
            )
            inscriptions.write({"state": "cancelled"})
            contracts = self.get_contracts()
            for contract in contracts:
                if contract.partner_id.id in inscriptions.mapped("partner_id").ids:
                    with contract_utils(self.env, contract) as component:
                        component.set_contract_status_closed(fields.Date.today())

    def _setup_selfconsumption_contract_line_description(
        self, distribution_id, contract
    ):
        for contract_line in contract.contract_line_ids:
            supply_point_assignation = distribution_id.supply_point_assignation_ids.filtered_domain(
                [
                    (
                        "supply_point_id",
                        "=",
                        int(
                            contract.sale_order_id.metadata_line_ids.filtered_domain(
                                [("key", "=", "supply_point_id")]
                            ).mapped("value")[0]
                        ),
                    ),
                ]
            )
            data = {
                "code": supply_point_assignation.supply_point_id.code,
                "owner_id": supply_point_assignation.supply_point_id.owner_id.display_name,
            }
            # Each invoicing type has different data in the description column, so we need to check and modify
            if self.selfconsumption_id.invoicing_mode == "energy_delivered":
                data["cau"] = self.selfconsumption_id.code
            elif self.selfconsumption_id.invoicing_mode == "power_acquired":
                data["cau"] = self.selfconsumption_id.code
                data["power"] = self.selfconsumption_id.power
                data["coefficient"] = supply_point_assignation.coefficient
                (
                    first_date_invoiced,
                    last_date_invoiced,
                    recurring_next_date,
                ) = contract_line._get_period_to_invoice(
                    contract_line.last_date_invoiced,
                    contract_line.recurring_next_date,
                )
                data["days_invoiced"] = (
                    (last_date_invoiced - first_date_invoiced).days + 1
                    if first_date_invoiced and last_date_invoiced
                    else 0
                )
                data["power_acquired"] = (
                    round(
                        self.selfconsumption_id.power
                        * supply_point_assignation.coefficient,
                        2,
                    )
                    if supply_point_assignation.coefficient
                    else 0.0
                )
                data["total_amount"] = round(
                    data["days_invoiced"] * data["power_acquired"], 2
                )
            contract_line._set_name(data)

    def action_selfconsumption_import_wizard(self):
        self.ensure_one()
        return {
            "name": _("Import Inscriptions and Supply Points"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "energy_selfconsumption.selfconsumption_import.wizard",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
        }

    def validate_state(self, state):
        if state not in ("activation", ACTIVE):
            error_message = _(
                "The report can be downloaded when the project is in activation or active status."
            )
            raise ValidationError(error_message)

    def action_export_csv_inscriptions_wizard(self):
        self.ensure_one()
        wizard = self.env["export.csv.inscritions.wizard"].with_context({
            "active_id": self.id,
        }).create({})
        return wizard.exportar_csv()
    
    def action_set_iban_inscriptions(self):
        self.ensure_one()
        return self.env.ref("energy_selfconsumption.action_set_iban_inscriptions").read()[0]

    def action_manager_authorization_report(self):
        self.ensure_one()
        self.validate_state(self.state)
        return self.env.ref(
            "energy_selfconsumption.selfconsumption_manager_authorization_report"
        ).report_action(self)

    def action_power_sharing_agreement_report(self):
        self.ensure_one()
        self.validate_state(self.state)
        return self.env.ref(
            "energy_selfconsumption.power_sharing_agreement_report"
        ).report_action(self)

    def action_manager_partition_coefficient_report(self):
        self.validate_state(self.state)
        tables_to_use = self.report_distribution_table
        file_content = ""
        if tables_to_use.type == "fixed":
            for table in tables_to_use:
                for assignation in table.supply_point_assignation_ids:
                    coefficient_format = f"{assignation.coefficient:.6f}"
                    file_content += f"{assignation.supply_point_id.code};{coefficient_format.replace('.', ',')}\r\n"
        else:
            file_data = base64.b64decode(
                tables_to_use.hourly_coefficients_imported_file
            )
            self.ensure_one()
            try:
                try:
                    decoded_file = file_data.decode(
                        tables_to_use.hourly_coefficients_imported_encoding
                    )
                except UnicodeDecodeError:
                    detected_encoding = chardet.detect(file_data).get("encoding", False)
                    if not detected_encoding:
                        raise ValidationError(
                            _("No valid encoding was found for the attached file")
                        )
                    decoded_file = file_data.decode(detected_encoding)

                df = pd.read_csv(
                    StringIO(decoded_file),
                    delimiter=tables_to_use.hourly_coefficients_imported_delimiter,
                    quotechar=tables_to_use.hourly_coefficients_imported_quotechar,
                )
                try:
                    for index, row in df.iterrows():
                        hour = int(row["hour"])
                        hour_str = str(hour).zfill(4)
                        for column in df.columns[1:]:
                            coefficient_format = f"{row[column]:.6f}"
                            file_content += f"{column};{hour_str};{coefficient_format.replace('.', ',')}\r\n"
                except Exception:
                    raise ValidationError(_("Error reading file"))
            except Exception:
                raise ValidationError(_("Error parsing the file"))

        file_content = file_content.encode("utf-8")

        date = datetime.now()
        year = date.strftime("%Y")
        report = self.env["energy_selfconsumption.coefficient_report"].create(
            {"report_data": file_content, "file_name": f"{self.code}_{year}.txt"}
        )
        url = "/energy_selfconsumption/download_report?id=%s" % report.id
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }

    def send_energy_delivery_invoicing_reminder(self):
        today = fields.date.today()
        date_validation = today + timedelta(days=3)

        projects = self.env["contract.contract"].read_group(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "=",
                    "energy_delivered",
                ),
                ("recurring_next_date", "=", date_validation),
            ],
            ["project_id"],
            ["project_id"],
        )
        template = self.env.ref(
            "energy_selfconsumption.selfconsumption_energy_delivered_invoicing_reminder",
            True,
        )
        for project in projects:
            # project["project_id"][0] - project.project_id.id
            selfconsumption_id = self.browse(project["project_id"][0])
            contract = selfconsumption_id.contract_ids[0]
            first_date = contract.next_period_date_start
            last_date = contract.next_period_date_end
            next_invoicing = contract.recurring_next_date
            ctx = {
                "next_invoicing": next_invoicing.strftime("%d-%m-%Y"),
                "first_date": first_date.strftime("%d-%m-%Y"),
                "last_date": last_date.strftime("%d-%m-%Y"),
            }
            template.with_context(ctx).send_mail(
                force_send=True,
                res_id=selfconsumption_id.id,
                email_layout_xmlid="mail.mail_notification_layout",
            )

    def send_energy_delivery_custom_invoicing_reminder(self):
        projects = self.env["contract.contract"].read_group(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "=",
                    "energy_custom",
                ),
                ("recurring_next_date", "=", fields.date.today()),
            ],
            ["project_id"],
            ["project_id"],
        )
        template = self.env.ref(
            "energy_selfconsumption.selfconsumption_energy_delivered_custom_invoicing_reminder",
            True,
        )
        for project in projects:
            # project["project_id"][0] - project.project_id.id
            selfconsumption_id = self.browse(project["project_id"][0])
            contract = selfconsumption_id.contract_ids[0]
            first_date = contract.next_period_date_start
            last_date = contract.next_period_date_end
            next_invoicing = contract.recurring_next_date
            ctx = {
                "next_invoicing": next_invoicing.strftime("%d-%m-%Y"),
                "first_date": first_date.strftime("%d-%m-%Y"),
                "last_date": last_date.strftime("%d-%m-%Y"),
            }
            template.with_context(ctx).send_mail(
                force_send=True,
                res_id=selfconsumption_id.id,
                email_layout_xmlid="mail.mail_notification_layout",
            )

    def send_power_acquired_invoicing_reminder(self):
        today = fields.date.today()
        projects = self.env["contract.contract"].read_group(
            [
                (
                    "project_id.selfconsumption_id.invoicing_mode",
                    "=",
                    "power_acquired",
                ),
                ("recurring_next_date", "=", today),
            ],
            ["project_id"],
            ["project_id"],
        )
        template = self.env.ref(
            "energy_selfconsumption.selfconsumption_power_acquired_invoicing_reminder",
            True,
        )
        for project in projects:
            # project["project_id"][0] - project.project_id.id
            selfconsumption_id = self.browse(project["project_id"][0])
            contract = selfconsumption_id.contract_ids[0]
            next_invoicing = contract.recurring_next_date
            ctx = {
                "next_invoicing": next_invoicing.strftime("%d-%m-%Y"),
            }
            template.with_context(ctx).send_mail(
                force_send=True,
                res_id=selfconsumption_id.id,
                email_layout_xmlid="mail.mail_notification_layout",
            )


class CoefficientReport(models.TransientModel):
    _name = "energy_selfconsumption.coefficient_report"
    _description = "Generate Partition Coefficient Report"

    report_data = fields.Text("Report Data", readonly=True)
    file_name = fields.Char("File Name", readonly=True)
