import logging

from odoo import SUPERUSER_ID, api, fields, models

logger = logging.getLogger(__name__)

from .res_company import _HIERARCHY_LEVEL_VALUES

_COMPANY_HIERARCHY_LEVEL = _HIERARCHY_LEVEL_VALUES + [("none", "NONE")]


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "user.currentcompany.mixin"]

    gender = fields.Selection(
        selection_add=[
            ("not_binary", "Not binary"),
            ("not_share", "I prefer to not share it"),
        ]
    )
    signup_token = fields.Char(
        groups="base.group_erp_manager,energy_communities.group_admin"
    )
    signup_type = fields.Char(
        groups="base.group_erp_manager,energy_communities.group_admin",
    )
    signup_expiration = fields.Datetime(
        groups="base.group_erp_manager,energy_communities.group_admin"
    )
    company_hierarchy_level = fields.Selection(
        _COMPANY_HIERARCHY_LEVEL,
        string="Company hierarchy level",
        default="none",
        compute="compute_company_hierarchy_level",
        store=True,
    )
    company_ids_info = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
        compute="_compute_company_ids_info",
        store=False,
    )

    @api.depends("company_ids")
    def _compute_company_ids_info(self):
        for record in self:
            record.company_ids_info = record.company_ids

    def compute_company_hierarchy_level(self):
        for record in self:
            rel_company = self.env["res.company"].search(
                [("partner_id", "=", record.id)]
            )
            if rel_company:
                record.company_hierarchy_level = rel_company.hierarchy_level

    @api.model
    def create(self, vals):
        new_partner = super().create(vals)
        current_user = self.env.user
        if (
            not new_partner.company_ids
            and
            # TODO: is really necessary user not being root or admin?
            current_user
            not in (
                self.env.ref("base.user_root"),
                self.env.ref("base.user_admin"),
            )
        ):
            new_partner.write(
                {"company_ids": [(4, current_user.get_current_company_id())]}
            )

        return new_partner

    def cron_update_company_ids_from_user(self):
        partner_with_users = self.search(
            [("user_ids", "!=", False), ("user_ids.id", "!=", SUPERUSER_ID)]
        )
        for partner in partner_with_users:
            logger.info(
                "Updated company_ids to partner {}".format(partner.display_name)
            )
            if partner.user_ids.company_ids.ids:
                partner.write({"company_ids": partner.user_ids.company_ids.ids})
        self.env["res.users"].browse(SUPERUSER_ID).partner_id.write(
            {"company_ids": False}
        )

    def get_cooperator_from_vat(self, vat, company_id=False):
        if vat:
            vat = vat.strip()
        # email could be falsy or be only made of whitespace.
        if not vat:
            return self.browse()
        domain = [("vat", "ilike", vat)]
        if company_id:
            domain.append(("company_ids", "in", int(company_id)))
        partner = self.search(domain, limit=1)
        return partner
