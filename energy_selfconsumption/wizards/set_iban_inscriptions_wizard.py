# -*- coding: utf-8 -*-
import logging
from stdnum.es import iban
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
        # Get inscriptions
        set_iban_inscriptions_line_wizard_ids = []
        for inscription in selfconsumption_id.inscription_ids:
            set_iban_inscriptions_line_wizard_ids.append((0, 0, {
                'inscription_id': inscription.id,
                'partner_id': inscription.partner_id.id,
                'iban': inscription.mandate_id and inscription.mandate_id.partner_bank_id and inscription.mandate_id.partner_bank_id.acc_number or '',
                'date_mandate': inscription.mandate_id and inscription.mandate_id.signature_date or '',
            }))
        default_fields['set_iban_inscriptions_line_wizard_ids'] = set_iban_inscriptions_line_wizard_ids
        return default_fields
    
    @api.model
    def default_get(self, default_fields):
        default_fields = super().default_get(default_fields)
        default_fields = self.get_default_inscriptions(default_fields)
        return default_fields

    def set_iban_inscriptions(self):
        if not self.set_iban_inscriptions_line_wizard_ids:
            raise ValidationError(_("There is no inscriptions to set."))
        for line in self.set_iban_inscriptions_line_wizard_ids:
            if not line.iban:
                _logger.warning(f"The IBAN field is empty for inscription {line.inscription_id.id}.")
                continue
            iban_number = line.iban.replace(" ", "")
            try:
                iban.validate(iban_number)
            except Exception as e:
                raise ValidationError(_(f"Invalid IBAN: {e}"))
            
            if not line.date_mandate:
                line.date_mandate = fields.Date.today()
                
            bank_account = (
                self.env["res.partner.bank"]
                .sudo()
                .search(
                    [
                        ("acc_number", "=", iban_number),
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
                            "acc_number": iban_number,
                            "partner_id": line.inscription_id.partner_id.id,
                            "company_id": line.inscription_id.partner_id.company_id.id,
                        }
                    )
                )

            mandate_obj = (
                self.env["account.banking.mandate"].sudo().search(
                    [
                        ("partner_bank_id", "=", bank_account.id),
                        ("partner_id", "=", line.inscription_id.partner_id.id),
                        ("company_id", "=", line.inscription_id.partner_id.company_id.id),
                    ],
                    limit=1,
                )
            )
            if not mandate_obj:
                mandate_obj = (
                    self.env["account.banking.mandate"]
                    .with_company(line.inscription_id.partner_id.company_id.id)
                    .sudo()
                    .create({
                        "partner_bank_id": bank_account.id,
                        "partner_id": line.inscription_id.partner_id.id,
                        "company_id": line.inscription_id.partner_id.company_id.id,
                        "signature_date": line.date_mandate,
                    })
                )
            line.inscription_id.write({"mandate_id":mandate_obj.id})
        selfconsumption_id = self.env['energy_selfconsumption.selfconsumption'].browse(self.env.context.get('active_id'))
        return selfconsumption_id.get_inscriptions_view()

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
    )
    
    date_mandate = fields.Date(
        string='Date mandate',
    )

    
