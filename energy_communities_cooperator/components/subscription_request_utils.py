from odoo import _

from odoo.addons.component.core import Component

from ..config import (
    MAPPING_SUBSCRIPTION_COMPONENT_ERROR_TITLE,
    STATUS_CODE_CONSISTENCY_ERROR,
    STATUS_CODE_SERVER_ERROR,
)
from ..exceptions import ComponentValidationError
from ..schemas.website_share_subscription_schemas import (
    SubscriptionRequestCreationParams,
)


class SubscriptionRequestUtils(Component):
    _name = "subscription.request.utils"
    _usage = "subscription.request.utils"
    _apply_on = "subscription.request"
    _collection = "utils.backend"

    def create_subscription_request(
        self,
        creation_params: SubscriptionRequestCreationParams,
    ):
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
            self._validate_creation_params(creation_params)
        except ComponentValidationError as e:
            raise e
        try:
            creation_params = self._get_model_creation_params(creation_params)
        except Exception as e:
            raise ComponentValidationError(
                STATUS_CODE_SERVER_ERROR,
                _("There is a problem on creating request params"),
                [
                    e.args[0],
                    _("Please contact the platform administrator to fix the issue."),
                ],
            )
        # Create subscription request
        try:
            subscription_request = (
                self.env["subscription.request"].sudo().create(creation_params)
            )
        except Exception as e:
            raise ComponentValidationError(
                STATUS_CODE_SERVER_ERROR,
                _("There is a problem on creating request."),
                [
                    e.args[0],
                    _("Please contact the platform administrator to fix the issue."),
                ],
            )
        self._validate_subscription_data_consistency(subscription_request)
        return subscription_request

    def _validate_creation_params(
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
        if creation_params.company_id.data_policy_approval_required:
            if (
                "privacy_policy" not in creation_params
                or creation_params.privacy_policy != "on"
            ):
                errors.append(_("Privacy policy must be approved"))
        # Validate internal rules approval
        if creation_params.company_id.internal_rules_approval_required:
            if (
                "internal_rules" not in creation_params
                or creation_params.internal_rules != "on"
            ):
                errors.append(_("Internal rules must be approved"))
        # Validate financial risk approval
        if creation_params.company_id.financial_risk_approval_required:
            if (
                "financial_risk" not in creation_params
                or creation_params.financial_risk != "on"
            ):
                errors.append(_("Financial risk must be approved"))
        # Validate generic rules approval
        if creation_params.company_id.generic_rules_approval_required:
            if (
                "generic_rules" not in creation_params
                or creation_params.generic_rules != "on"
            ):
                errors.append(_("Generic rules must be approved"))
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
        # TODO: Validate privacy_policy and conditions_payment must be marked
        if errors:
            raise ComponentValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
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

    def _get_model_creation_params(
        self, creation_params: SubscriptionRequestCreationParams
    ) -> dict:
        creation_params = creation_params.model_dump()
        if creation_params["membertype_mode"].value == "company":
            creation_params["is_company"] = "on"
        data_policy_approved = False
        if creation_params["company_id"].display_data_policy_approval:
            data_policy_approved = (
                True if creation_params["privacy_policy"] == "on" else False
            )
        internal_rules_approved = False
        if creation_params["company_id"].display_internal_rules_approval:
            internal_rules_approved = (
                True if creation_params["internal_rules"] == "on" else False
            )
        financial_risk_approved = False
        if creation_params["company_id"].display_financial_risk_approval:
            financial_risk_approved = (
                True if creation_params["financial_risk"] == "on" else False
            )
        generic_rules_approved = False
        if creation_params["company_id"].display_generic_rules_approval:
            generic_rules_approved = (
                True if creation_params["generic_rules"] == "on" else False
            )
        creation_params |= {
            "source": "website",  # TODO review diferent type of creation
            "gender": creation_params["gender"].value,
            "data_policy_approved": data_policy_approved,
            "internal_rules_approved": internal_rules_approved,
            "financial_risk_approved": financial_risk_approved,
            "generic_rules_approved": generic_rules_approved,
            "country_id": creation_params["country_id"].id,
            "share_product_id": creation_params[
                "share_product_id"
            ].product_variant_id.id,
            "company_id": creation_params["company_id"].id,
        }
        # Delete not necesary params for creation
        del creation_params["product_categ"]
        del creation_params["membertype_mode"]
        del creation_params["privacy_policy"]
        del creation_params["conditions_payment"]
        return creation_params
