from odoo import _, api, fields, models


class CrmTeam(models.Model):
    _name = "crm.team"
    _inherit = "crm.team"

    is_default_team = fields.Boolean(string="Is default team")

    @api.model
    def get_create_default_sale_team(self, company):
        if company.hierarchy_level != "instance":
            existing_team = (
                self.env["crm.team"]
                .sudo()
                .search(
                    [("company_id", "=", company.id), ("is_default_team", "=", True)]
                )
            )
            if not existing_team:
                return (
                    self.env["crm.team"]
                    .sudo()
                    .create(
                        {
                            "name": company.name,
                            "use_opportunities": True,
                            "company_id": company.id,
                            "is_default_team": True,
                        }
                    )
                )
            else:
                return existing_team[0]
        else:
            return self.env.ref("sales_team.team_sales_department")
