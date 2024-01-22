from odoo import _, api, fields, models


class AssignCRMToCoordinatorCompanyWizard(models.TransientModel):
    _name = "assign.crm.to.coordinator.company.wizard"
    _description = "Assign CRM to coordinator company wizard"

    crm_lead_id = fields.Many2one("crm.lead")
    assigned_company_id = fields.Many2one(
        "res.company",
        string="Assigned company",
        required=True,
        domain=[("hierarchy_level", "=", "coordinator")],
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        defaults["crm_lead_id"] = self.env.context["active_id"]
        return defaults

    def assign_to_coordinator_company(self):
        self.ensure_one()
        self.remove_follower()
        new_crm_lead = self.crm_lead_id.sudo().copy(
            {"team_id": None, "user_id": None, "stage_id": 1}  # New
        )
        new_crm_lead.write({"company_id": self.assigned_company_id})
        new_crm_msg = _(
            "Opportunity assigned to Coordinator %s (ID: %s), where %s is the id of the original instance-level record."
            % (self.assigned_company_id.name, new_crm_lead.id, self.crm_lead_id.id)
        )
        new_crm_lead.message_post(body=new_crm_msg)
        self.crm_lead_id.write({"stage_id": 4, "ce_child_lead_id": new_crm_lead})  # Won
        won_crm_msg = _(
            "Opportunity created from Instance opportunity with ID %s, where %s is the id of the new record generated at the Coordinator level"
            % (self.crm_lead_id.id, new_crm_lead.id)
        )
        self.crm_lead_id.message_post(body=won_crm_msg)
        crm_lead_metadata = self.env["crm.lead.metadata.line"].search(
            [("crm_lead_id", "=", self.crm_lead_id.id)]
        )
        for metadata in crm_lead_metadata:
            new_crm_lead_metadata = metadata.copy({"crm_lead_id": new_crm_lead.id})
        self.add_follower()

    def remove_follower(self):
        instance_admin = self.env.ref("energy_communities.role_ce_manager").id
        company_id = self.crm_lead_id.company_id.id
        followers = self.env["res.users"].search(
            [
                ("role_line_ids.role_id", "=", instance_admin),
                ("company_ids.id", "=", company_id),
            ]
        )
        if followers:
            self.crm_lead_id.message_unsubscribe(partner_ids=followers.partner_id.ids)

    def add_follower(self):
        coordinator_admin = self.env.ref("energy_communities.role_coord_admin").id
        company_id = self.crm_lead_id.company_id.id
        followers = self.env["res.users"].search(
            [
                ("role_line_ids.role_id", "=", coordinator_admin),
                ("company_ids.id", "=", company_id),
            ]
        )
        if followers:
            self.crm_lead_id.message_subscribe(partner_ids=followers.partner_id.ids)
            # notify followers
            email_values = {"email_to": followers.mapped("partner_id.email")}
            template = self.env.ref(
                "energy_communities.email_templ_lead_assigned_to_coordinator_id"
            ).with_context(email_values)
            self.crm_lead_id.message_post_with_template(template.id)
