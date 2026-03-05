from odoo import _

from odoo.addons.component.core import Component

from ..config import MAPPING_SUBSCRIPTION_COMPONENT_ERROR_TITLE
from ..exceptions import ComponentValidationError
from ..models.subscription_request import SubscriptionRequest
from ..schemas.website_share_subscription_schemas import (
    MemberShipMode,
    MemberTypeMode,
    SubscriptionMode,
    SubscriptionRequestCreationParams,
)


class SubscriptionRequestUtils(Component):
    _name = "subscription.request.utils"
    _usage = "subscription.request.utils"
    _apply_on = "subscription.request"
    _collection = "utils.backend"

    def create_subscription_request_params(
        self, form_submission, ctx
    ) -> SubscriptionRequestCreationParams:
        creation_params = form_submission.model_dump()
        creation_params["share_product_id"] = (
            self.env["product.template"]
            .sudo()
            .search([("id", "=", form_submission.share_product_id)])
        )
        creation_params["product_categ"] = ctx.product_categ
        creation_params["company_id"] = ctx.company
        creation_params["membertype_mode"] = ctx.membertype_mode
        creation_params["membership_mode"] = ctx.membership_mode
        creation_params["is_company"] = ctx.membertype_mode == MemberTypeMode.company
        creation_params["source"] = "website"  # TODO review diferent type of creation
        creation_params["data_policy_approved"] = form_submission.privacy_policy
        creation_params["mandate_approved"] = form_submission.conditions_payment

        if ctx.subscription_mode.value == SubscriptionMode.voluntary:
            partner = self._get_partner_form(form_submission, ctx)
            creation_params |= (
                self._get_subscription_request_creation_params_from_partner(partner)
            )
        else:  # memeber or company_member or invited or company_invites
            creation_params["gender"] = form_submission.gender
            creation_params["generic_rules_approved"] = form_submission.generic_rules
            creation_params["internal_rules_approved"] = form_submission.internal_rules
            creation_params["financial_risk_approved"] = form_submission.financial_risk
            creation_params["country_id"] = (
                self.env["res.country"]
                .sudo()
                .search([("id", "=", form_submission.country_id)])
            )
            lang_model = (
                self.env["res.lang"].sudo().search([("id", "=", form_submission.lang)])
            )
            if lang_model:
                creation_params["lang"] = lang_model.code
            else:
                creation_params["lang"] = ""

        return SubscriptionRequestCreationParams(**creation_params)

    def create_subscription_request(
        self,
        creation_params: SubscriptionRequestCreationParams,
    ) -> SubscriptionRequest:
        """
        Create subscription request with validation.

        Validates and prepares values before creating the subscription request.
        Also handles file attachments if provided.

        Args:
            values: Dictionary with subscription request data
            kwargs: Original kwargs dictionary (optional, for validation)
            logged: Boolean indicating if user is logged in (optional)
            post_file: List of file attachments (optional)

        Returns:
            Created subscription.request recordset
        """
        try:
            self._validate_subscription_request_params(creation_params)
            subscription_request = (
                self.env["subscription.request"]
                .sudo()
                .create(creation_params.model_dump())
            )
        except Exception as e:
            raise ComponentValidationError(
                _("There is a problem on creating request params"),
                [
                    e.args[0],
                    _("Please contact the platform administrator to fix the issue."),
                ],
            ) from e
        self._validate_subscription_data_consistency(subscription_request)
        return subscription_request

    def _validate_subscription_request_params(
        self, creation_params: SubscriptionRequestCreationParams
    ):
        errors = []
        min_qty = creation_params.share_product_id.minimum_quantity
        if creation_params.ordered_parts < min_qty:
            errors.append(_(f"Oder part must be higher than product config {min_qty}"))
        # Validate subscription maximum amount
        if creation_params.company_id.subscription_maximum_amount != 0.0:
            if (
                creation_params.share_product_id.list_price
                * creation_params.ordered_parts
                > creation_params.company_id.subscription_maximum_amount
            ):
                errors.append(
                    _(
                        f"Subscription maximum amount is {creation_params.share_product_id.list_price * creation_params.ordered_parts} but the maximum amount is {creation_params.company_id.subscription_maximum_amount}"
                    )
                )
        # Validate data policy approval
        privacy_must_approved = (
            creation_params.company_id.display_data_policy_approval
            and creation_params.company_id.data_policy_approval_required
        )
        if privacy_must_approved and not creation_params.data_policy_approved:
            errors.append(_("Privacy policy must be approved"))
        # Validate generic rules approval
        generic_rules_must_approved = (
            creation_params.company_id.display_generic_rules_approval
            and creation_params.company_id.generic_rules_approval_required
        )
        if generic_rules_must_approved and not creation_params.generic_rules_approved:
            errors.append(_("Generic rules must be approved"))
        # Validate internal rules approval
        internal_rules_must_approved = (
            creation_params.company_id.display_internal_rules_approval
            and creation_params.company_id.internal_rules_approval_required
        )
        if internal_rules_must_approved and not creation_params.internal_rules_approved:
            errors.append(_("Internal rules must be approved"))
        # Validate financial risk approval
        financial_risk_must_approved = (
            creation_params.company_id.display_financial_risk_approval
            and creation_params.company_id.financial_risk_approval_required
        )
        if financial_risk_must_approved and not creation_params.financial_risk_approved:
            errors.append(_("Financial risk must be approved"))
        # Product must belong to company
        if creation_params.company_id != creation_params.share_product_id.company_id:
            errors.append(
                _(
                    f"Product {creation_params.share_product_id.name} must belong to company {creation_params.company_id.name}"
                )
            )
        # Product must have correct subrciption context
        if creation_params.share_product_id.categ_id != creation_params.product_categ:
            errors.append(
                _(
                    f"Product {creation_params.share_product_id.name} must have correct subscription context"
                )
            )

        # Existing partner
        partners = (
            self.env["res.partner"]
            .sudo()
            .search([("vat", "ilike", creation_params.vat), ("parent_id", "=", False)])
        )
        existing_partner = any(
            [
                bool(
                    partner._get_member_or_candidate_cooperative_membership(
                        creation_params.company_id.id
                    )
                )
                for partner in partners
            ]
        )
        if (
            existing_partner
            and creation_params.membership_mode != MemberShipMode.voluntary
        ):
            errors.append(
                _(
                    "There is an existing account for this"
                    " vat number on this community. "
                    "Please contact with the community administrators."
                )
            )

        # TODO: Validate privacy_policy and conditions_payment must be marked
        if errors:
            raise ComponentValidationError(
                MAPPING_SUBSCRIPTION_COMPONENT_ERROR_TITLE["general"],
                errors,
            )
        return True

    # TODO: Do we need to validate more fields that might change? Wich ones?
    def _validate_subscription_data_consistency(self, subscription_request):
        consistency_errors = []
        subscription_partner = subscription_request.partner_id
        if subscription_partner:
            if subscription_partner.email != subscription_request.email:
                consistency_errors.append(
                    "Partner Email: {}".format(subscription_partner.email)
                )
            if subscription_partner.phone != subscription_request.phone:
                consistency_errors.append(
                    "Partner Phone: {}".format(subscription_partner.phone)
                )
        if consistency_errors:
            error_html_list = "<ul>"
            for error in consistency_errors:
                error_html_list += "<li>{}</li>".format(error)
            error_html_list += "</ul>"
            subscription_request.message_post(
                **{
                    "subject": "We found partner discrepancy in the form",
                    "body": "<p>The contact information received from the form <b>was diferent</b> from the one saved in the partner:</p><p>{}</p>".format(
                        error_html_list
                    ),
                }
            )

    def _get_partner_form(self, form_submission, ctx):
        partner_vat = form_submission.vat.strip().upper()
        partner = (
            self.env["res.partner"]
            .sudo()
            .get_cooperator_from_vat(partner_vat, ctx.company.id)
        )
        if not partner:
            raise FormValidationError(
                MAPPING_FORM_ERROR_TITLE["general"],
                [_("We couldn't find a member with %s", creation_params["vat"])],
            )
        return partner

    def _get_subscription_request_creation_params_from_partner(self, partner):
        return {
            "partner_id": partner.id,
            "already_cooperator": partner.member,
            "email": partner.email or _("Email not found"),
            "phone": partner.phone or _("Phone not found"),
            "gender": partner.gender or "not_share",
            "lastname": partner.lastname or _("Lastname not found"),
            "firstname": partner.firstname or partner.name,
            "address": partner.street or _("Address not found"),
            "city": partner.city or _("City not found"),
            "zip_code": partner.zip or _("ZIP code not found"),
            "country_id": (partner.country_id or ctx.company.default_country_id),
            "lang": partner.lang or ctx.company.default_lang_id.id,
            "birthdate": partner.birthdate_date.strftime("%d/%m/%Y") or False,
        }
