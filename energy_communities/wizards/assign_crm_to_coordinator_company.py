from odoo import fields, models


class AssignCRMToCoordinatorCompanyWizard(models.TransientModel):
    _name = 'assign.crm.to.coordinator.company.wizard'
    crm_lead_id = fields.Many2one('crm.lead')
    summary = fields.Char(required=True)
    assigned_company_id = fields.Many2one(
        'res.company',
        string='Assign to company',
        required=True,
    )

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        defaults['crm_lead_id'] = self.env.context['active_id']
        return defaults

    def button_assign_to_coordinator_company(self):
        self.ensure_one()
        self.crm_lead_id.write({'company_id': self.assigned_company_id})
