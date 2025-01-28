from odoo import fields, models


class ContractAbstractContract(models.AbstractModel):
    _inherit = "contract.abstract.contract"
    _check_company_auto = False

    company_id = fields.Many2one(
        required=False,
        default=None,
    )
