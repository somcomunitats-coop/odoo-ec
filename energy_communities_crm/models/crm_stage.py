from odoo import api, fields, models


class Stage(models.Model):
    _name = "crm.stage"
    _inherit = "crm.stage"

    # is_default_stage = fields.Boolean(string="Is default stage")
    original_stage_id = fields.Many2one("crm.stage")

    @api.model
    def get_create_default_stages_dict(self, company):
        stage_1, stage_2, stage_3, stage_4 = self.get_create_default_stages(company)
        return {
            stage_1.original_stage_id.id: stage_1,
            stage_2.original_stage_id.id: stage_2,
            stage_3.original_stage_id.id: stage_3,
            stage_4.original_stage_id.id: stage_4,
        }

    @api.model
    def get_create_default_stages(self, company):
        system_stage_1 = self.env.ref("crm.stage_lead1")
        system_stage_2 = self.env.ref("crm.stage_lead2")
        system_stage_3 = self.env.ref("crm.stage_lead3")
        system_stage_4 = self.env.ref("crm.stage_lead4")
        if company.hierarchy_level != "instance":
            return (
                self.get_duplicate_stage(system_stage_1, company),
                self.get_duplicate_stage(system_stage_2, company),
                self.get_duplicate_stage(system_stage_3, company),
                self.get_duplicate_stage(system_stage_4, company),
            )
        else:
            return (
                system_stage_1,
                system_stage_2,
                system_stage_3,
                system_stage_4,
            )

    @api.model
    def get_duplicate_stage(self, system_stage, company):
        default_sale_team = self.env["crm.team"].get_create_default_sale_team(company)
        existing_stage = (
            self.env["crm.stage"]
            .sudo()
            .search(
                [
                    ("team_id", "=", default_sale_team.id),
                    ("original_stage_id", "=", system_stage.id),
                ]
            )
        )
        if not existing_stage:
            return system_stage.sudo().copy(
                {
                    "name": system_stage.name + " - " + default_sale_team.name,
                    "original_stage_id": system_stage.id,
                    "team_id": default_sale_team.id,
                }
            )
        else:
            return existing_stage[0]
