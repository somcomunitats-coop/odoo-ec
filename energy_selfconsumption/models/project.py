from odoo import fields, models

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.energy_communities_service_invoicing.utils import IN_PROGRESS


class EnergyProject(models.Model):
    _inherit = "energy_project.project"

    selfconsumption_id = fields.One2many(
        "energy_selfconsumption.selfconsumption", "project_id"
    )
    contract_ids = fields.One2many("contract.contract", "project_id", readonly=True)

    def get_member_contract(self, member: Partner):
        self.ensure_one()
        member_contract = self.contract_ids.filtered(
            lambda contract: contract.partner_id == member
            and contract.status == IN_PROGRESS
        )
        return member_contract
