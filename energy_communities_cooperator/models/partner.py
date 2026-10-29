from odoo import _, api, fields, models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = "res.partner"

    # validate=False keeps stored types of other communities writable while the
    # dropdown of the contact filter only lists the active company's shares.
    cooperator_type = fields.Selection(
        selection="_get_share_type",
        validate=False,
    )

    @api.depends_context("company")
    def _get_share_type(self):
        return self.env["product.template"].get_company_share_type_selection(
            self.env.company
        )

    gender = fields.Selection(
        selection_add=[
            ("not_binary", "Not binary"),
            ("not_share", "I prefer to not share it"),
        ]
    )
    company_register_number = fields.Char(
        string="Company Register Number",
        compute="_compute_company_register_number",
        store=True,
    )

    no_member_autorized_in_energy_actions = fields.Boolean(
        string="Authorized guest",
        company_dependent=True,
        help="Enable the contact to participate in Community Energy Actions despite not being an effective member of the Community.",
    )
    effective_invited = fields.Boolean(
        string="Effective Invited",
        compute="_compute_effective_invited",
        store=True,
        default=False,
    )

    @api.depends(
        "cooperative_membership_ids", "cooperative_membership_ids.effective_invited"
    )
    def _compute_effective_invited(self):
        for record in self:
            record.effective_invited = (
                record.cooperative_membership_ids.filtered(
                    lambda x: x.effective_invited == True
                )
                or False
            )

    @api.depends("vat")
    def _compute_company_register_number(self):
        for record in self:
            if record.is_company:
                record.company_register_number = record.vat

    def get_partner_membership_for_company(self, company_id):
        self.ensure_one()
        return (
            self.env["cooperative.membership"]
            .sudo()
            .search([("partner_id", "=", self.id), ("company_id", "=", company_id.id)])
        )

    def _get_member_or_candidate_cooperative_membership(self, company_id):
        self.ensure_one()
        return (
            self.env["cooperative.membership"]
            .sudo()
            .search_count(
                [
                    "&",
                    "&",
                    ("partner_id", "=", self.id),
                    ("company_id", "=", company_id),
                    "|",
                    ("member", "=", True),
                    ("coop_candidate", "=", True),
                ]
            )
        )
