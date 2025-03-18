import logging

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError

logger = logging.getLogger(__name__)

from .res_company import _HIERARCHY_LEVEL_VALUES

_COMPANY_HIERARCHY_LEVEL = _HIERARCHY_LEVEL_VALUES + [("none", "NONE")]


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "user.currentcompany.mixin"]

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
    related_company_id = fields.Many2one(
        "res.company",
        string="Represented company",
        compute="compute_related_company_id",
        store=False,
    )
    company_ids_info = fields.Many2many(
        string="Companies",
        comodel_name="res.company",
        compute="_compute_company_ids_info",
        store=False,
    )
    has_rel_user = fields.Boolean(compute="_compute_has_rel_user", store=False)

    @api.depends("company_ids")
    def _compute_company_ids_info(self):
        for record in self:
            record.company_ids_info = record.company_ids

    @api.depends("user_ids")
    def _compute_has_rel_user(self):
        for record in self:
            if record.user_ids:
                record.has_rel_user = True
            else:
                record.has_rel_user = False

    def compute_company_hierarchy_level(self):
        for record in self:
            record.company_hierarchy_level = "none"
            if record.related_company_id:
                record.company_hierarchy_level = (
                    record.related_company_id.hierarchy_level
                )

    def compute_related_company_id(self):
        for record in self:
            record.related_company_id = False
            related_company_id = (
                self.env["res.company"]
                .sudo()
                .search([("partner_id", "=", record.id)], limit=1)
            )
            if related_company_id:
                record.related_company_id = related_company_id[0].id

    @api.constrains("company_ids")
    def _constrains_partner_company_ids(self):
        for record in self:
            for rpb in record.bank_ids:
                if rpb.company_id not in record.company_ids:
                    raise ValidationError(
                        _(
                            "You cannot remove company {} because there are banks referencing to it"
                        ).format(rpb.company_id.name)
                    )

    @api.model_create_multi
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

    # TODO: Rename this method. It has nothing to do with cooperator
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
