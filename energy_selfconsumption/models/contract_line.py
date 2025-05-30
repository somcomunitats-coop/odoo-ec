from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ContractLine(models.Model):
    _inherit = "contract.line"

    main_line = fields.Boolean("Main line", default=False)

    @api.constrains("main_line")
    def _check_only_one_main_line(self):
        for line in self:
            contract_lines = line.contract_id.contract_line_ids
            main_lines = contract_lines.filtered(lambda l: l.main_line)
            if len(main_lines) > 1:
                raise ValidationError("There can only be one main line per contract.")
