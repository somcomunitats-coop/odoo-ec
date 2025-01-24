from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.tools.translate import _


class ContractContract(models.Model):
    _inherit = "contract.contract"

    community_company_id = fields.Many2one(
        "res.company",
        string="Related community",
        domain="[('hierarchy_level','=','community')]",
    )
    predecessor_contract_id = fields.Many2one(
        "contract.contract", string="Predecessor contract"
    )

    def action_activate_contract(self):
        return self._action_contract("activate")

    def action_close_contract(self):
        return self._action_contract("close")

    def action_modify_contract(self):
        return self._action_contract("modification")

    def _action_contract(self, action):
        self.ensure_one()
        wizard = self.env["service.invoicing.action.wizard"].create(
            {"service_invoicing_id": self.id, "executed_action": action}
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Executing: {}").format(action),
            "res_model": "service.invoicing.action.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }
