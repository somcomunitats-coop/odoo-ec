from odoo import api, fields, models


class Stage(models.Model):
    _name = "crm.stage"
    _inherit = "crm.stage"

    @api.model
    def default_get(self, fields):
        """Hack update :  when going from the pipeline, creating a stage with a sales team in
        context should create a stage for the current Sales Team only. If no default_stage we'll
        add to context the default stage for the current user company.
        https://github.com/odoo/odoo/blob/14.0/addons/crm/models/crm_stage.py#L26
        """
        ctx = dict(self.env.context)
        ctx.update({"crm_team_mono": True})
        if not ctx.get("search_default_team_id"):
            ctx.update(
                {
                    "default_team_id": self.env[
                        "crm.team"
                    ].get_create_default_sale_team(self.env.company)
                }
            )
        return super(Stage, self.with_context(ctx)).default_get(fields)

    # is_default_stage = fields.Boolean(string="Is default stage")
    original_stage_id = fields.Many2one("crm.stage")

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
                    "original_stage_id": system_stage.id,
                    "team_id": default_sale_team.id,
                }
            )
        else:
            return existing_stage[0]
