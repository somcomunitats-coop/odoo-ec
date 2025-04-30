# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Set_iban_inscriptions_wizard(models.TransientModel):
    _name = 'energy_selfconsumption.set_iban_inscriptions_wizard'
    _description = _('Set_iban_inscriptions')

    set_iban_inscriptions_line_wizard_ids = fields.One2many(
        'energy_selfconsumption.set_iban_inscriptions_line_wizard',
        'set_iban_inscriptions_wizard_id',
        string='Set_iban_inscriptions_line_wizard',
    )

    def get_default_inscriptions(self, default_fields):
        selfconsumption_id = self.env['energy_selfconsumption.selfconsumption'].browse(self.env.context.get('active_id'))
        if not selfconsumption_id:
            raise ValidationError(_("There is no selfconsumption."))
        # Get distribution table
        distribution_id = (
            self.selfconsumption_id.distribution_table_ids.filtered_domain(
                [("state", "=", "process")]
            )
        )
        if not distribution_id:
            raise ValidationError(
                _("There is no distribution table in proces of activation.")
            )
        # Get inscriptions
        inscriptions_ids = distribution_id.selfconsumption_project_id.inscription_ids.mapped(
                "partner_id.supply_ids"
            ).filtered_domain(
                [
                    (
                        "id",
                        "not in",
                        distribution_id.supply_point_assignation_ids.mapped(
                            "supply_point_id.id"
                        ),
                    )
                ]
            )
        set_iban_inscriptions_line_wizard_ids = []
        for inscription in inscriptions_ids:
            if not inscription.acc_number:
                set_iban_inscriptions_line_wizard_ids.append((0, 0, {
                    'inscription_id': inscription.id,
                    'partner_id': inscription.partner_id.id,
                }))

        default_fields['set_iban_inscriptions_line_wizard_ids'] = set_iban_inscriptions_line_wizard_ids
        return default_fields
    
    @api.model
    def default_get(self, default_fields):
        default_fields = self.get_default_inscriptions(default_fields)
        return super().default_get(default_fields)

    def set_iban_inscriptions(self):
        if not self.set_iban_inscriptions_line_wizard_ids:
            raise ValidationError(_("There is no inscriptions to set."))
        for line in self.set_iban_inscriptions_line_wizard_ids:
            if not line.iban:
                _logger.warning(f"The IBAN field is empty for inscription {line.inscription_id.id}.")
                continue
            try:
                line.iban.validate(line.iban)
            except Exception as e:
                return True, _("Invalid IBAN: {error}").format(error=e)
            
            if not line.date_mandate:
                line.date_mandate = fields.Date.today()
                
            bank_account = (
                self.env["res.partner.bank"]
                .sudo()
                .search(
                    [
                        ("acc_number", "=", line.iban),
                        ("partner_id", "=", line.inscription_id.partner_id.id),
                        ("company_id", "=", line.inscription_id.partner_id.company_id.id),
                    ]
                )
            )

            if not bank_account:
                bank_account = (
                    self.env["res.partner.bank"]
                    .sudo()
                    .create(
                        {
                            "acc_number": line.iban,
                            "partner_id": line.inscription_id.partner_id.id,
                            "company_id": line.inscription_id.partner_id.company_id.id,
                        }
                    )
                )
            mandate_obj = (
                self.env["account.banking.mandate"]
                .with_company(line.inscription_id.partner_id.company_id.id)
                .sudo()
                .search(
                    [
                        ("partner_bank_id", "=", bank_account.id),
                        ("partner_id", "=", line.inscription_id.partner_id.id),
                        ("company_id", "=", line.inscription_id.partner_id.company_id.id),
                    ],
                    limit=1,
                )
            )
            line.inscription_id.mandate_id = mandate_obj
            return True

class Set_iban_inscriptions_line_wizard(models.TransientModel):
    _name = 'energy_selfconsumption.set_iban_inscriptions_line_wizard'
    _description = _('Set_iban_inscriptions_line')

    set_iban_inscriptions_wizard_id = fields.Many2one(
        'energy_selfconsumption.set_iban_inscriptions_wizard',
        string='Set_iban_inscriptions_wizard',
        required=True,
    )

    inscription_id = fields.Many2one(
        'energy_selfconsumption.inscription_selfconsumption',
        string='Inscription',
        required=True,
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
    )

    iban = fields.Char(
        string='IBAN',
        required=True,
    )
    
    date_mandate = fields.Date(
        string='Date mandate',
        required=True,
    )

    
