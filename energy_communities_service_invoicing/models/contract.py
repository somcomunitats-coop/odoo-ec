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
