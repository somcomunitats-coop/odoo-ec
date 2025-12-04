from datetime import datetime

from odoo import _
from odoo.tools import date_type

from odoo.addons.component.core import Component

from ..config import (
    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
    CONTEXT_STATUS_CODE_NOT_FOUND_ERROR,
    CONTEXT_VALIDATION_ERROR_TITLE,
)
from ..exceptions import ContextValidationError
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
            creation_params = self._get_model_creation_params(creation_params)
        except Exception as e:
            raise e
        # Create subscription request
        try:
            subscription_request = (
                self.env["subscription.request"].sudo().create(creation_params)
            )
        except Exception as e:
            raise e
        return subscription_request

    def _validate_creation_params(
        self, creation_params: SubscriptionRequestCreationParams
    ):
        min_qty = creation_params.share_product_id.minimum_quantity
        if creation_params.ordered_parts < min_qty:
            raise ValueError(
                _(f"Oder part must be higher than product config {min_qty}")
            )
        # TODO: company.subscription_maximum_amount ??
        # Product must belong to company
        # Product must have correct subrciption context
        # TODO: Validate privacy_policy and conditions_payment must be marked
        return True

    def _get_model_creation_params(
        self, creation_params: SubscriptionRequestCreationParams
    ) -> dict:
        creation_params = creation_params.model_dump()
        if creation_params["membertype_mode"].value == "company":
            creation_params["is_company"] = "on"
        creation_params |= {
            # TODO: Check this config
            # "display_data_policy": creation_params["company_id"].display_data_policy_approval,
            # "data_policy_required": creation_params["company_id"].data_policy_approval_required,
            # "data_policy_text": creation_params["company_id"].data_policy_approval_text,
            # "display_internal_rules": creation_params["company_id"].display_internal_rules_approval,
            # "internal_rules_required": creation_params["company_id"].internal_rules_approval_required,
            # "internal_rules_text": creation_params["company_id"].internal_rules_approval_text,
            # "display_financial_risk": creation_params["company_id"].display_financial_risk_approval,
            # "financial_risk_required": creation_params["company_id"].financial_risk_approval_required,
            # "financial_risk_text": creation_params["company_id"].financial_risk_approval_text,
            # "display_generic_rules": creation_params["company_id"].display_generic_rules_approval,
            # "generic_rules_required": creation_params["company_id"].generic_rules_approval_required,
            # "generic_rules_text": creation_params["company_id"].generic_rules_approval_text,
            "source": "website",  # TODO review diferent type of creation
            "gender": creation_params["gender"].value,
            "data_policy_approved": True,
            "internal_rules_approved": True,
            "financial_risk_approved": True,
            "generic_rules_approved": True,
            "country_id": creation_params["country_id"].id,
            "share_product_id": creation_params[
                "share_product_id"
            ].product_variant_id.id,
            "company_id": creation_params["company_id"].id,
            "birthdate": datetime.strptime(
                creation_params["birthdate"], "%d/%m/%Y"
            ).date(),
        }
        # Delete not necesary params for creation
        del creation_params["product_categ"]
        del creation_params["membertype_mode"]
        del creation_params["privacy_policy"]
        del creation_params["conditions_payment"]
        return creation_params
