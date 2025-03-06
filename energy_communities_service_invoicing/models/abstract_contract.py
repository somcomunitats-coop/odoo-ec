from odoo import fields, models


class ContractAbstractContract(models.AbstractModel):
    _inherit = "contract.abstract.contract"
    _check_company_auto = False

    company_id = fields.Many2one(
        required=False,
        default=None,
    )


class ContractAbstractContractLine(models.AbstractModel):
    _inherit = "contract.abstract.contract.line"

    price_unit = fields.Float(
        string="Unit Price",
        compute="_compute_price_unit",
        inverse="_inverse_price_unit",
        digits="Product Price",
    )
    price_subtotal = fields.Float(
        compute="_compute_price_subtotal", string="Sub Total", digits="Product Price"
    )
