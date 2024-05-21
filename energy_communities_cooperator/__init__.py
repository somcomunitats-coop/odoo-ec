from . import controllers
from . import models

from odoo import fields, api
from odoo.addons.cooperator.models import partner


def add_company_dependent_related_field(
    model_class, delegate, name, field_type, **kwargs
):
    delegate_field_name = ".".join([delegate, name])

    def _compute(self):
        for record in self:
            setattr(record, name, getattr(getattr(record, delegate), name))

    def _set(self):
        for record in self:
            delegate_record = getattr(record, delegate)
            setattr(delegate_record, name, getattr(record, name))

    def _search(self, operator, value):
        return [(delegate_field_name, operator, value)]

    setattr(
        model_class,
        name,
        field_type(
            **kwargs,
            compute=api.depends_context("company")(
                api.depends(delegate_field_name)(_compute)
            ),
            inverse=_set,
            search=_search,
        ),
    )


def post_load_cooperator_memberships():
    partner.add_company_dependent_related_field = add_company_dependent_related_field
    partner.add_cooperative_membership_field(
        "cooperator",
        fields.Boolean,
        string="Cooperator",
        help="Check this box if this contact is a cooperator (effective or not).",
    )
    partner.add_cooperative_membership_field(
        "member",
        fields.Boolean,
        string="Effective cooperator",
        help="Check this box if this cooperator is an effective member.",
        readonly=True,
    )
    partner.add_cooperative_membership_field(
        "coop_candidate",
        fields.Boolean,
        string="Cooperator candidate",
        readonly=True,
    )
    partner.add_cooperative_membership_field(
        "old_member",
        fields.Boolean,
        string="Old cooperator",
        help="Check this box if this cooperator is no more an effective member.",
    )
    partner.add_cooperative_membership_field(
        "cooperator_register_number",
        fields.Integer,
        string="Cooperator Number",
        readonly=True,
    )
    partner.add_cooperative_membership_field(
        "number_of_share",
        fields.Integer,
        string="Number of share",
        readonly=True,
    )
    partner.add_cooperative_membership_field(
        "total_value",
        fields.Float,
        string="Total value of shares",
        readonly=True,
    )
    partner.add_cooperative_membership_field(
        "cooperator_type",
        fields.Selection,
        selection=partner.ResPartner._get_share_type,
        string="Cooperator Type",
        readonly=True,
    )
    partner.add_cooperative_membership_field(
        "effective_date",
        fields.Date,
        string="Effective Date",
        readonly=True,
    )
    partner.add_cooperative_membership_field(
        "data_policy_approved",
        fields.Boolean,
        string="Approved Data Policy",
    )
    partner.add_cooperative_membership_field(
        "internal_rules_approved",
        fields.Boolean,
        string="Approved Internal Rules",
    )
    partner.add_cooperative_membership_field(
        "financial_risk_approved",
        fields.Boolean,
        string="Approved Financial Risk",
    )
    partner.add_cooperative_membership_field(
        "generic_rules_approved",
        fields.Boolean,
        string="Approved generic rules",
    )
