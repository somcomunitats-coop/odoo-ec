import base64
import re
from datetime import datetime

from odoo import _

from odoo.addons.component.core import Component

from ..config import (
    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
    CONTEXT_STATUS_CODE_NOT_FOUND_ERROR,
    CONTEXT_VALIDATION_ERROR_TITLE,
)
from ..exceptions import ContextValidationError

from .. schemas import SubscriptionRequestCreationParams


class SubscriptionRequestUtils(Component):
    _name = "subscription.request.utils"
    _usage = "subscription.request.utils"
    _apply_on = "subscription.request"
    _collection = "utils.backend"

    def validate_and_prepare_values(
            self,
            creation_params: SubscriptionRequestCreationParam
    ):
        return True
        """
        Validate and prepare values for subscription request creation.

        Based on the validation logic from WebsiteShareSubscriptionController.
        Uses field names from the new controller (e.g., "ordered_parts", "privacy_policy").
        Also supports backward compatibility with old field names for migration purposes.

        Field names used by new controller:
        - ordered_parts (instead of nb_parts)
        - privacy_policy (instead of data_policy_approved)
        - conditions_payment (for payment conditions)
        - email (for both individual and company subscriptions)
        - share_product_id (product template ID, converted to variant)

        Validates required fields, email, IBAN, files, and prepares data for creation.

        Args:
            kwargs: Dictionary with form submission data from WebsiteShareSubscriptionController
            logged: Boolean indicating if user is logged in
            post_file: List of file attachments (optional)

        Returns:
            Dictionary with validated and prepared values for subscription request

        Raises:
            ContextValidationError: If validation fails
        """
        sub_req_obj = self.env["subscription.request"]
        user_obj = self.env["res.users"]
        company = self.env["res.company"].browse(kwargs.get("company_id"))

        if not company:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_NOT_FOUND_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                _("Company is required"),
            )

        values = {}
        post_file = post_file or []

        # Filter and prepare values from kwargs
        # Exclude blacklisted fields and technical fields
        blacklist = {
            "id",
            "create_uid",
            "create_date",
            "write_uid",
            "write_date",
            "user_id",
            "active",
        }

        for field_name, field_value in kwargs.items():
            if hasattr(field_value, "filename") and field_value:
                # File handling is done separately
                continue
            elif (
                field_name in sub_req_obj._fields
                and field_name not in blacklist
                and field_value
            ):
                values[field_name] = field_value

        # Determine if company subscription
        # Check both old format (is_company="on") and new format (is_company=True)
        is_company = (
            kwargs.get("is_company") == "on" or kwargs.get("is_company") is True
        )

        # Get email - new controller uses "email" for both individual and company
        email = kwargs.get("email")
        # Fallback to old format if needed
        if is_company and not email:
            email = kwargs.get("company_email")

        # Validate required fields
        required_fields = sub_req_obj.sudo().get_required_field()
        missing_fields = [field for field in required_fields if not values.get(field)]

        if missing_fields:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                _("Some mandatory fields have not been filled: %s")
                % ", ".join(missing_fields),
            )

        # Validate email if not logged
        if not logged and email:
            # Check if user already exists
            user = user_obj.sudo().search([("login", "=", email)], limit=1)
            if user:
                raise ContextValidationError(
                    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                    CONTEXT_VALIDATION_ERROR_TITLE,
                    _(
                        "An account already exists for this email address. "
                        "Please log in before filling in the form."
                    ),
                )

            # Validate email confirmation (new controller may not always send confirm_email)
            confirm_email = kwargs.get("confirm_email")
            if confirm_email and email != confirm_email:
                raise ContextValidationError(
                    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                    CONTEXT_VALIDATION_ERROR_TITLE,
                    _("Email and confirmation email addresses don't match."),
                )

            # Set confirm_email for internal use
            values["confirm_email"] = email

        # Validate ID card upload if required
        if company.allow_id_card_upload and not post_file:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                _("Please upload a scan of your ID card."),
            )

        # Validate IBAN if required
        if "iban" in required_fields:
            iban = kwargs.get("iban", "").strip()
            if iban:
                # Check if check_iban method exists (from cooperator base module)
                if hasattr(sub_req_obj, "check_iban"):
                    valid = sub_req_obj.check_iban(iban)
                    if not valid:
                        raise ContextValidationError(
                            CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                            CONTEXT_VALIDATION_ERROR_TITLE,
                            _("Provided IBAN is not valid."),
                        )
                # Basic IBAN format validation if method doesn't exist
                elif len(iban) < 15 or len(iban) > 34:
                    raise ContextValidationError(
                        CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                        CONTEXT_VALIDATION_ERROR_TITLE,
                        _("Provided IBAN format is not valid."),
                    )

        # Process logged user data
        already_coop = False
        if logged:
            partner = self.env.user.partner_id
            values["partner_id"] = partner.id
            already_coop = partner.member

        values["already_cooperator"] = already_coop
        values["is_company"] = is_company

        # Process approval checkboxes
        # New controller uses "privacy_policy" instead of "data_policy_approved"
        privacy_policy = kwargs.get("privacy_policy")
        if privacy_policy == "on" or privacy_policy is True:
            values["data_policy_approved"] = True
        # Also support old format for backward compatibility
        elif kwargs.get("data_policy_approved", "off") == "on":
            values["data_policy_approved"] = True

        # Support other approval fields if present
        if kwargs.get("internal_rules_approved", "off") == "on":
            values["internal_rules_approved"] = True

        if kwargs.get("financial_risk_approved", "off") == "on":
            values["financial_risk_approved"] = True

        if kwargs.get("generic_rules_approved", "off") == "on":
            values["generic_rules_approved"] = True

        # New controller uses "conditions_payment" for payment conditions
        conditions_payment = kwargs.get("conditions_payment")
        if conditions_payment == "on" or conditions_payment is True:
            # Map to appropriate field if needed
            pass

        # Process personal information
        if kwargs.get("lastname"):
            values["lastname"] = kwargs.get("lastname")

        if kwargs.get("firstname"):
            values["firstname"] = kwargs.get("firstname")

        # Process birthdate
        if kwargs.get("birthdate"):
            try:
                values["birthdate"] = datetime.strptime(
                    kwargs.get("birthdate"), "%d-%m-%Y"
                ).date()
            except ValueError:
                raise ContextValidationError(
                    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                    CONTEXT_VALIDATION_ERROR_TITLE,
                    _("Invalid birthdate format. Use DD-MM-YYYY."),
                )

        # Set source
        values["source"] = kwargs.get("source", "website")

        # Process share product
        # New controller uses "share_product_id" directly (product template ID)
        share_product_id = kwargs.get("share_product_id")
        if share_product_id:
            try:
                # Try to get product variant from template
                share_product_template = (
                    self.env["product.template"].sudo().browse(int(share_product_id))
                )
                if share_product_template.product_variant_ids:
                    values[
                        "share_product_id"
                    ] = share_product_template.product_variant_ids[0].id
                else:
                    raise ContextValidationError(
                        CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                        CONTEXT_VALIDATION_ERROR_TITLE,
                        _("Product template has no variants."),
                    )
            except (ValueError, IndexError, AttributeError):
                # If it's already a variant ID, use it directly
                try:
                    variant = (
                        self.env["product.product"].sudo().browse(int(share_product_id))
                    )
                    if variant.exists():
                        values["share_product_id"] = variant.id
                    else:
                        raise ContextValidationError(
                            CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                            CONTEXT_VALIDATION_ERROR_TITLE,
                            _("Invalid share product selected."),
                        )
                except (ValueError, AttributeError):
                    raise ContextValidationError(
                        CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                        CONTEXT_VALIDATION_ERROR_TITLE,
                        _("Invalid share product selected."),
                    )
        else:
            raise ContextValidationError(
                CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                CONTEXT_VALIDATION_ERROR_TITLE,
                _("Share product is required."),
            )

        # Process ordered parts (new controller uses "ordered_parts")
        ordered_parts = kwargs.get("ordered_parts")
        if ordered_parts:
            try:
                values["ordered_parts"] = float(ordered_parts)
            except (ValueError, TypeError):
                raise ContextValidationError(
                    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                    CONTEXT_VALIDATION_ERROR_TITLE,
                    _("Invalid ordered parts value."),
                )
        # Support old format "nb_parts" for backward compatibility
        elif kwargs.get("nb_parts"):
            try:
                values["ordered_parts"] = float(kwargs.get("nb_parts"))
            except (ValueError, TypeError):
                raise ContextValidationError(
                    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                    CONTEXT_VALIDATION_ERROR_TITLE,
                    _("Invalid number of parts value."),
                )

        # Note: total_price from form is calculated field, not stored in model
        # The model calculates total from ordered_parts * share_product_id.list_price

        # Process company register number for companies
        if is_company and kwargs.get("company_register_number"):
            values["company_register_number"] = re.sub(
                "[^0-9a-zA-Z]+", "", kwargs.get("company_register_number")
            )

        # Ensure company_id is integer
        if "company_id" in values:
            try:
                values["company_id"] = int(values["company_id"])
            except (ValueError, TypeError):
                raise ContextValidationError(
                    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                    CONTEXT_VALIDATION_ERROR_TITLE,
                    _("Invalid company ID."),
                )

        # Ensure country_id is integer
        if "country_id" in values:
            try:
                values["country_id"] = int(values["country_id"])
            except (ValueError, TypeError):
                raise ContextValidationError(
                    CONTEXT_STATUS_CODE_CONSISTENCY_ERROR,
                    CONTEXT_VALIDATION_ERROR_TITLE,
                    _("Invalid country ID."),
                )

        # Setup company_register_number from VAT if not set
        if "vat" in values and not values.get("company_register_number"):
            values["company_register_number"] = values["vat"]

        return values

    def create_subscription_request(
        self, creation_params: SubscriptionRequestCreationParam
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
            self.validate_creation_params(creation_params)
        except Exception as e:
            raise e

        # Create subscription request
        subscription_request = self.env["subscription.request"].sudo().create(creation_params.model_dump())

        return subscription_request
