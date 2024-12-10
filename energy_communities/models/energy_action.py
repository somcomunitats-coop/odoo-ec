from odoo import _, api, fields, models


class EnergyAction(models.Model):
    _name = "energy.action"
    _description = "Energy action"

    name = fields.Char(string="Name", translate=True)
    xml_id = fields.Char(compute="_compute_xml_id", string="External ID")
    company_mids = fields.Many2many(
        "res.company",
        "res_company_energy_action_rel",
        "energy_action_id",
        "company_id",
        string="Related companies",
    )

    def _compute_xml_id(self):
        res = self.get_external_id()
        for record in self:
            record.xml_id = res.get(record.id)
