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

    def action_activate_contract(self):
        return self._action_contract("activate")

    def action_close_contract(self):
        return self._action_contract("close")

    def _action_contract(self, action):
        self.ensure_one()
        wizard = self.env["service.invoicing.action.wizard"].create(
            {"service_invoicing_id": self.id, "executed_action": action}
        )
        return {
            "type": "ir.actions.act_window",
            # "name": _("Activate srvice invoicing"),
            "res_model": "service.invoicing.action.wizard",
            "view_type": "form",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard.id,
        }
