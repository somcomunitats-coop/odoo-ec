from odoo.exceptions import ValidationError
from odoo.tools.translate import _

from odoo.addons.component.core import Component


class UserCreator(Component):
    _name = "user.creator"
    _usage = "user.create"
    _apply_on = "res.users"
    _collection = "utils.backend"

    def _validate_create_users_from_cooperator_partners(self) -> bool:
        if len(self.env.context["allowed_company_ids"]) > 1:
            raise ValidationError(
                _(
                    "This wizard can only run with ONE company selected."
                    " Please limit the context of the selected companies to one."
                )
            )
        return True

    def _validate_create_users_from_communities_cooperator_partners(
        self, communities
    ) -> bool:
        if communities.filtered(
            lambda community: community.hierarchy_level != "community"
        ):
            raise ValidationError(
                _("There is at least one selected no community companies")
            )
        return True

    def create_users_from_cooperator_partners(
        self, partners, role_id, action, force_invite
    ) -> None:
        self._validate_create_users_from_cooperator_partners()
        company_id = self.env["res.company"].browse(
            self.env.context["allowed_company_ids"]
        )
        for partner in partners:
            cooperator = self.env["cooperative.membership"].search(
                [
                    ("partner_id", "=", partner.id),
                    ("company_id", "=", company_id.id),
                    ("cooperator", "=", True),
                    ("member", "=", True),
                ]
            )
            if cooperator:
                # TODO: refactor this in order to being called from component
                self.env["res.users"].with_delay().build_platform_user(
                    company_id,
                    partner,
                    role_id,
                    action,
                    force_invite,
                    user_vals={},
                )

    def create_users_from_communities_cooperator_partners(
        self, communities, role_id, action, force_invite
    ) -> None:
        self._validate_create_users_from_communities_cooperator_partners(communities)
        for community in communities:
            # TODO: Check if we really need a sudo
            cooperators = (
                self.env["cooperative.membership"]
                .sudo()
                .search(
                    [
                        ("company_id", "=", community.id),
                        ("cooperator", "=", True),
                        ("member", "=", True),
                    ]
                )
            )
            for cooperator in cooperators:
                self.env["res.users"].with_delay().build_platform_user(
                    community,
                    cooperator.partner_id,
                    role_id,
                    action,
                    force_invite,
                    user_vals={},
                )
