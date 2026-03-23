import logging
import traceback
from http import HTTPMethod, HTTPStatus

from pydantic import ValidationError as PydanticValidationError

from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from ..config import (
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_FINANCIAL_RISK,
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_GENERIC_RULES,
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_INTERNAL_RULES,
    MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PRIVACY_POLICY,
    MAPPING__PAYMENT_METHOD,
    MAPPING__SUBSCRIPTION_MODE__DEFAULT_FORM_FIELDS,
    MAPPING__SUBSCRIPTION_MODE__MEMBERSHIP_MODE,
    MAPPING__SUBSCRIPTION_MODE__MEMBERTYPE_MODE,
    MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF,
    MAPPING_FORM_ERROR_TITLE,
    MAPPING_FORM_SUCCESS,
    _get_headline_fixed_sepa_message,
    _get_headline_fixed_transfer_message,
    _get_subscription_mode_headline_message,
    _get_subscription_mode_page_title_message,
)
from ..exceptions import (
    ComponentValidationError,
    ControllerContextValidationError,
    FormValidationError,
    URLValidationError,
)
from ..schemas import (
    SubscriptionMode,
    SubscriptionRequestCreationParams,
    WebsiteShareSubscriptionContext,
    WebsiteShareSubscriptionSubmissionBase,
    WebsiteShareSubscriptionSubmissionCompanyMember,
    WebsiteShareSubscriptionSubmissionVoluntary,
)
from ..utils import convert_errors, subscription_request_utils

_logger = logging.getLogger(__name__)


class WebsiteShareSubscriptionController(http.Controller):
    """
    Controller for handling share subscription forms on the website.
    Manages form rendering and processing for different subscription modes.
    """

    @http.route(
        [
            "/subscription/<string:subscription_mode>/<string:company_ext_id>",
            "/subscription/<string:subscription_mode>/<string:company_ext_id>/<string:product_ext_id>",
        ],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
        csrf=False,  # TODO: this must be removed by correctly implementing test
    )
    def share_subscription_form(self, **kwargs):
        """
        Main route handler for share subscription forms.

        Handles both GET (form display) and POST (form submission) requests.
        Creates context from URL parameters and renders appropriate template.

        Args:
            **kwargs: URL parameters including subscription_mode, company_ext_id, and optional product_ext_id

        Returns:
            Rendered template with form data or error page if validation fails
        """
        # Create and validate context, handle validation errors
        try:
            # Build context creation parameters from URL kwargs
            ctx = self._get_website_share_subscription_context(kwargs)
            values = self._get_page_values(ctx)
            if request.httprequest.method == HTTPMethod.GET:
                return self._render_page(values, HTTPStatus.OK)
            if request.httprequest.method == HTTPMethod.POST:
                values = self._process_form(ctx)
        except (ControllerContextValidationError, URLValidationError) as e:
            # Render error page if context validation fails
            return self._render_error_page(e)
        except FormValidationError as e:
            _logger.error(traceback.format_exc())
            _logger.error(str(e))
            values["error"] = {"title": e.title, "messages": e.messages}
            self._populate_form_values_from_submission(request, values)
            return self._render_page(values, e.http_error_code)
        except Exception as e:
            _logger.error(traceback.format_exc())
            _logger.error(str(e))
            return self._render_error_page(e)

        return self._render_successfullpage()

    def _process_form(self, ctx):
        """
        Process form submission data using SubscriptionRequestUtils component.

        Validates and creates subscription request from form data.

        Args:
            ctx: WebsiteShareSubscriptionContext containig all context information
        """
        try:
            form_submission = self._get_requested_form(ctx.subscription_mode)
            with subscription_request_utils(request.env, ctx.company) as component:
                subscription_request_params = component.get_subscription_request_params(
                    form_submission, ctx
                )
                subscription_request = component.create_subscription_request(
                    subscription_request_params
                )
                component._check_subscription_data_consistency(subscription_request)
        except PydanticValidationError as e:
            raise FormValidationError(
                MAPPING_FORM_ERROR_TITLE["general"],
                self._get_errors_arr(e),
            )
        except ComponentValidationError as e:
            raise FormValidationError(e.title, e.messages)
        else:
            return self._get_page_base_values(ctx) | {
                "form_submitted": True,
                "success_msg": MAPPING_FORM_SUCCESS["general"],
            }

    def _populate_form_values_from_submission(self, request, values):
        form_submission = dict(request.httprequest.form)
        for field in values["form_fields"]:
            field_key = field.get("key")
            if field_key in form_submission:
                field["value"] = form_submission[field_key]

    # getters
    def _get_requested_form(self, subscription_mode: SubscriptionMode):
        # Extract form data from request
        if subscription_mode.value == SubscriptionMode.voluntary:
            form_submission = WebsiteShareSubscriptionSubmissionVoluntary(
                **request.httprequest.form
            )
        elif subscription_mode.value == SubscriptionMode.company_member:
            form_submission = WebsiteShareSubscriptionSubmissionCompanyMember(
                **request.httprequest.form
            )
        else:
            form_submission = WebsiteShareSubscriptionSubmissionBase(
                **request.httprequest.form
            )
        return form_submission

    def _get_errors_arr(self, e):
        return convert_errors(e)

    def _get_website_share_subscription_context(
        self, kwargs
    ) -> WebsiteShareSubscriptionContext:
        """
        Extracts and processes URL parameters to build context creation dictionary.
        Maps subscription mode to membership and member type modes, retrieves company
        and product category, and determines form type and available products.

        Args:
            kwargs: URL parameters from route

        Returns:
           A websiteShareSubscriptionContext instance
        """
        # Extract subscription mode from URL
        subscription_mode = kwargs.get("subscription_mode")

        # Map subscription mode to membership mode (member, invited, voluntary)
        membership_mode = MAPPING__SUBSCRIPTION_MODE__MEMBERSHIP_MODE.get(
            subscription_mode
        )

        # Map subscription mode to member type mode (individual, company)
        membertype_mode = MAPPING__SUBSCRIPTION_MODE__MEMBERTYPE_MODE.get(
            subscription_mode
        )

        # Determine form type: single (specific product) or generic (product selector)
        formtype_mode = self._get_formtype_mode(kwargs)

        # Retrieve company record from external ID
        company = self._get_model_from_ext_id(
            "res.company", "company_external_id", kwargs.get("company_ext_id")
        )

        # Get product category for this subscription mode
        product_categ = self._get_product_categ(subscription_mode, company)

        # Retrieve specific product if product_ext_id is provided
        query_product = self._get_model_from_ext_id(
            "product.template", "product_external_id", kwargs.get("product_ext_id")
        )

        # Combine base parameters with product information
        subscription_ctx = {
            "membership_mode": membership_mode,
            "membertype_mode": membertype_mode,
            "subscription_mode": subscription_mode,
            "formtype_mode": formtype_mode,
            "company": company,
            "product_categ": product_categ,
        } | self._get_page_products_dict(
            company, product_categ, query_product, formtype_mode, membertype_mode
        )
        return WebsiteShareSubscriptionContext(**subscription_ctx)

    def _get_page_values(self, ctx):
        """
        Build complete dictionary of values for page rendering.

        Combines context data with page-specific values (title, headlines) and form fields.

        Args:
            ctx: WebsiteShareSubscriptionContext instance

        Returns:
            Dictionary with all values needed for template rendering
        """
        values = self._get_page_base_values(ctx) | self._get_page_form_fields_values(
            ctx
        )
        return values

    def _get_page_base_values(self, ctx):
        """
        Get base page values: title and headlines for different payment methods.

        Args:
            ctx: WebsiteShareSubscriptionContext instance

        Returns:
            Dictionary with page_title and page_headline values
        """
        return ctx.model_dump() | {
            "page_title": self._get_page_title(ctx),
            "page_headline": self._get_page_headline(ctx),
            "page_headline_fixed_transfer": self._get_page_headline_fixed_transfer(ctx),
            "page_headline_fixed_sepa": self._get_page_headline_fixed_sepa(ctx),
        }

    def _get_page_products_dict(
        self, company, product_categ, query_product, formtype_mode, membertype_mode
    ):
        """
        Get products dictionary for page rendering.

        Returns either a single product (if formtype_mode is "single") or searches
        for available products based on category, company, and member type.

        Args:
            company: Company recordset
            product_categ: Product category recordset
            query_product: Specific product if provided in URL
            formtype_mode: "single" or "generic"
            membertype_mode: "individual" or "company"

        Returns:
            Dictionary with "products" (recordset) and "product" (single record)
        """
        # Single product mode: use the product from URL
        if formtype_mode == "single":
            return {"products": query_product, "product": query_product}

        # Generic mode: search for available products
        if product_categ and company:
            # Build domain for product search
            domain = [
                ("categ_id", "=", product_categ.id),
                ("company_id", "=", company.id),
                ("display_on_website", "=", True),
                ("is_share", "=", True),
            ]

            # Add member type filter
            if membertype_mode == "individual":
                domain.append(("by_individual", "=", True))
            elif membertype_mode == "company":
                domain.append(("by_company", "=", True))

            # Search products ordered by default_share_product (most relevant first)
            products = (
                request.env["product.template"]
                .sudo()
                .search(domain, order="default_share_product desc")
            )
            if products:
                return {"products": products, "product": products[0]}

        # Return None if no products found
        return {"products": None, "product": None}

    def _get_formtype_mode(self, kwargs):
        """
        Determine form type mode based on URL parameters.

        Args:
            kwargs: URL parameters

        Returns:
            "single" if product_ext_id is provided, "generic" otherwise
        """
        if "product_ext_id" in kwargs:
            return "single"
        return "generic"

    def _get_model_from_ext_id(self, model_name, field_name, ext_id):
        """
        Retrieve a record from a model using external ID field.

        Args:
            model_name: Odoo model name (e.g., "res.company")
            field_name: Field name containing external ID (e.g., "company_external_id")
            ext_id: External ID value to search for

        Returns:
            Recordset if found, False otherwise
        """
        if ext_id:
            return request.env[model_name].sudo().search([(field_name, "=", ext_id)])
        return False

    def _get_product_categ(self, subscription_mode, company):
        """
        Get product category for given subscription mode.

        Args:
            subscription_mode: Subscription mode string

        Returns:
            Product category recordset if found, None otherwise
        """
        try:
            categ = request.env.ref(
                MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF.get(subscription_mode)
            )
        except:
            categ = None
        if categ:
            return categ.sudo().with_company(company)
        return categ

    def _get_page_form_fields_values(self, ctx):
        """
        Build form fields values dictionary for template rendering.

        Iterates through configured form fields for the subscription mode,
        creates field dictionaries with all necessary attributes, and applies
        custom field updates based on context.

        Args:
            ctx: WebsiteShareSubscriptionContext instance

        Returns:
            Dictionary with "form_fields" list containing field configurations
        """
        # Get form fields configuration for this subscription mode
        form_fields = MAPPING__SUBSCRIPTION_MODE__DEFAULT_FORM_FIELDS[
            ctx.subscription_mode
        ].copy()
        # TODO: Add id card upload field if ctx.company.allow_id_card_upload is True
        have_clauses = False
        if ctx.company.display_generic_rules_approval:
            if not have_clauses:
                form_fields |= {
                    "h3_clauses": {
                        "key": "h3_clauses",
                        "class": "col-md-12",
                        "type": "form_h3",
                        "description": _("Clauses"),
                    },
                }
                have_clauses = True
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_GENERIC_RULES["generic_rules"][
                "description"
            ] = ctx.company.generic_rules_approval_text
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_GENERIC_RULES["generic_rules"][
                "required"
            ] = ctx.company.generic_rules_approval_required
            form_fields |= MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_GENERIC_RULES
        if ctx.company.display_internal_rules_approval:
            if not have_clauses:
                form_fields |= {
                    "h3_clauses": {
                        "key": "h3_clauses",
                        "class": "col-md-12",
                        "type": "form_h3",
                        "description": _("Clauses"),
                    },
                }
                have_clauses = True
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_INTERNAL_RULES["internal_rules"][
                "description"
            ] = ctx.company.internal_rules_approval_text
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_INTERNAL_RULES["internal_rules"][
                "required"
            ] = ctx.company.internal_rules_approval_required
            form_fields |= MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_INTERNAL_RULES
        if ctx.company.display_financial_risk_approval:
            if not have_clauses:
                form_fields |= {
                    "h3_clauses": {
                        "key": "h3_clauses",
                        "class": "col-md-12",
                        "type": "form_h3",
                        "description": _("Clauses"),
                    },
                }
                have_clauses = True
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_FINANCIAL_RISK["financial_risk"][
                "description"
            ] = ctx.company.financial_risk_approval_text
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_FINANCIAL_RISK["financial_risk"][
                "required"
            ] = ctx.company.financial_risk_approval_required
            form_fields |= MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_FINANCIAL_RISK
        if ctx.company.display_data_policy_approval:
            if not have_clauses:
                form_fields |= {
                    "h3_clauses": {
                        "key": "h3_clauses",
                        "class": "col-md-12",
                        "type": "form_h3",
                        "description": _("Clauses"),
                    },
                }
                have_clauses = True
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PRIVACY_POLICY["privacy_policy"][
                "description"
            ] = ctx.company.data_policy_approval_text
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PRIVACY_POLICY["privacy_policy"][
                "required"
            ] = ctx.company.data_policy_approval_required
            form_fields |= MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_PRIVACY_POLICY

        values = {"form_fields": []}

        # Build field dictionary for each configured field
        for field in form_fields:
            values_field = {
                "value": self._get_form_field_value(
                    ctx.model_dump(), form_fields[field].get("value", False)
                ),
                "key": field,
                "class": form_fields[field]["class"],
                "label": form_fields[field].get("label", False),
                "type": "energy_communities.{}".format(form_fields[field]["type"]),
                "disabled": form_fields[field].get("disabled", False),
                "required": form_fields[field].get("required", False),
                "description": form_fields[field].get("description", False),
                "options": form_fields[field].get("options", False),
                "readonly": form_fields[field].get("readonly", False),
            }
            # Apply custom field updates based on context
            self._update_form_custom_fields(ctx, values_field)
            values["form_fields"].append(values_field)
        return values

    def _get_page_title(self, ctx):
        """
        Get page title for subscription form.

        Args:
            ctx: WebsiteShareSubscriptionContext instance

        Returns:
            Formatted page title string
        """
        return _get_subscription_mode_page_title_message(
            ctx.subscription_mode, ctx.company.comercial_name
        )

    def _get_page_headline(self, ctx):
        """
        Get main page headline for subscription form.

        Args:
            ctx: WebsiteShareSubscriptionContext instance

        Returns:
            Formatted headline string
        """

        empty_headline = "<p><br></p>"

        if (
            ctx.formtype_mode.value == "single"
            and ctx.product.html_specific_products
            and ctx.product.html_specific_products != empty_headline
        ):
            return ctx.product.html_specific_products
        if (
            ctx.formtype_mode.value == "generic"
            and ctx.product_categ.share_form_header_text
            and ctx.product_categ.share_form_header_text != empty_headline
        ):
            return ctx.product_categ.share_form_header_text
        return _get_subscription_mode_headline_message(
            ctx.subscription_mode,
            ctx.company.comercial_name,
            ctx.company.company_external_id,
        )

    def _get_page_headline_fixed_transfer(self, ctx):
        """
        Get page headline for fixed price transfer payment method.

        Includes product price and currency symbol formatted for display.

        Args:
            ctx: WebsiteShareSubscriptionContext instance

        Returns:
            Formatted headline string with price and currency
        """
        return _get_headline_fixed_transfer_message(
            ctx.subscription_mode,
            str(ctx.product.list_price).replace(".", ","),
            ctx.company.currency_id.symbol,
        )

    def _get_page_headline_fixed_sepa(self, ctx):
        """
        Get page headline for fixed price SEPA payment method.

        Includes product price and currency symbol formatted for display.

        Args:
            ctx: WebsiteShareSubscriptionContext instance

        Returns:
            Formatted headline string with price and currency
        """
        return _get_headline_fixed_sepa_message(
            ctx.subscription_mode,
            str(ctx.product.list_price).replace(".", ","),
            ctx.company.currency_id.symbol,
        )

    # TODO: Adjust all this methods to new "_get_page_form_fields_values" method
    def _get_form_field_value(self, data, path):
        """
        Extract field value from nested data structure using dot notation path.

        Supports accessing nested dictionary keys and recordset attributes.
        Handles tuples (for selection fields) and converts recordsets to dictionaries.

        Args:
            data: Dictionary or recordset containing the data
            path: Dot-separated path to the field (e.g., "company.currency_id.symbol")
                  or boolean value

        Returns:
            Field value if found, empty string if not found, or boolean if path is boolean
        """
        # Return boolean value directly if path is boolean

        # Split path into keys

        try:
            key, path_attributes = path.split(".", 1)
        except (ValueError, AttributeError):
            return path

        current = data[key]
        for attr in path_attributes.split("."):
            # Handle tuple values (selection fields return tuples)
            if isinstance(current, tuple):
                return current[1]

            # Move to next level
            current = getattr(current, attr, "")
        return current

    def _get_country_options(self):
        """
        Get list of country options for dropdown field.

        Returns list with default "Select your country" option plus all countries
        ordered by name.

        Returns:
            List of dictionaries with "id" and "name" keys
        """
        return (
            request.env["res.country"]
            .sudo()
            .search([], order="name")
            .mapped(lambda x: {"id": x.id, "name": x.name})
        )

    def _get_lang_options(self):
        """
        Get list of language options for dropdown field.

        Returns list with default "Select your language" option plus all active
        languages ordered by name.

        Returns:
            List of dictionaries with "id" and "name" keys
        """
        return (
            request.env["res.lang"]
            .sudo()
            .search([("active", "=", True)], order="name")
            .mapped(lambda x: {"id": x.id, "name": x.name})
        )

    def _get_share_product_options(self, ctx):
        """
        Build list of share product options for dropdown field.

        For each product, determines payment method (SEPA or transfer) and builds
        option dictionary with product ID, name, price, and payment method.

        Args:
            ctx: WebsiteShareSubscriptionContext instance

        Returns:
            List of dictionaries with product information for dropdown options
        """
        options = []
        for product in ctx.products:
            # Default payment method is transfer
            payment_method = "transfer"

            # Check if product has SEPA payment method configured
            if (
                product.payment_mode_id
                and product.payment_mode_id.payment_method_id
                and product.payment_mode_id.payment_method_id.id
                == request.env.ref(MAPPING__PAYMENT_METHOD["sepa"]).id
            ):
                payment_method = "sepa"
            # Check if product has transfer payment method configured
            elif (
                product.payment_mode_id
                and product.payment_mode_id.payment_method_id
                and product.payment_mode_id.payment_method_id.id
                == request.env.ref(MAPPING__PAYMENT_METHOD["transfer"]).id
            ):
                payment_method = "transfer"

            # Build option dictionary with extra attributes in a structured way
            # This allows dynamic generation of data-* attributes in templates
            # Build data_attrs dictionary with HTML-ready attribute names
            data_attrs = {
                "data-list-price": product.list_price
                if product.list_price is not None
                else 0.00,
                "data-payment-method": payment_method,
                "data-minimum-quantity": product.minimum_quantity
                if product.minimum_quantity is not None
                else 1,
            }
            options.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "data_attrs": data_attrs,
                }
            )
        return options

    # updaters
    # We must used it to control share product selector behaviour
    def _update_form_custom_fields(self, ctx, values_field):
        """
        Update form field values based on field key and context.

        Modifies values_field dictionary in place with dynamic values, options,
        and disabled states based on context. This method is used to control
        share product selector behaviour and other dynamic field configurations.

        Args:
            ctx: WebsiteShareSubscriptionContext instance containing form context
            values_field: Dictionary representing a form field that will be modified in place
        """
        # Update currency symbol field value from company currency
        if values_field["key"] == "currency_symbol":
            values_field["value"] = ctx.company.currency_id.symbol

        # Update country dropdown options with available countries
        if values_field["key"] == "country_id":
            values_field["options"] = self._get_country_options()

        # Update language dropdown options with available languages
        if values_field["key"] == "lang":
            values_field["options"] = self._get_lang_options()

        # Update share product dropdown options and disable if only one product available
        if values_field["key"] == "share_product_id":
            values_field["options"] = self._get_share_product_options(ctx)
            # Disable selector when only one product is available (no choice needed)
            if len(ctx.products) == 1:
                values_field["readonly"] = True

        if not ctx.product_categ.product_website:
            if values_field["key"] == "share_product_id":
                values_field["class"] = "col-md-4 d-none"
                values_field["required"] = False
                values_field["readonly"] = True
            if values_field["key"] == "ordered_parts":
                values_field["class"] = "col-md-3 d-none"
                values_field["required"] = False
                values_field["readonly"] = True
            if values_field["key"] == "total_price":
                values_field["class"] = "col-md-4 d-none"
                values_field["required"] = False
                values_field["readonly"] = True
            if values_field["key"] == "currency_symbol":
                values_field["class"] = "col-md-1 d-none"
                values_field["required"] = False
                values_field["readonly"] = True
            if values_field["key"] == "h3_share_selection":
                values_field["class"] = "col-md-12 d-none"

        if ctx.product_categ.product_qty_must_be_read_only:
            if values_field["key"] == "ordered_parts":
                values_field["readonly"] = True

    # Render methods
    def _render_successfullpage(self):
        return request.render("energy_communities.website_form_submit_confirmation")

    def _render_page(self, values, status_code):
        """
        Render the subscription page template with provided values.

        Args:
            values: Dictionary containing all data needed for template rendering

        Returns:
            Rendered template response
        """
        return request.render(
            "energy_communities_cooperator.template_subscription_page",
            values,
            status=status_code,
        )

    def _render_error_page(self, error: Exception):
        """
        Render the subscription page template with provided values.

        Args:
            values: Dictionary containing all data needed for template rendering

        Returns:
            Rendered template response
        """
        name = type(error).__name__

        if isinstance(error, (ComponentValidationError, FormValidationError)):
            error_message = "\n".join(error.messages)
        elif isinstance(error, ControllerContextValidationError):
            error_message = error.message
        else:
            error_message = str(error)
        status_code = getattr(
            error, "http_error_code", HTTPStatus.INTERNAL_SERVER_ERROR
        )
        return request.render(
            "http_routing.http_error",
            {
                "status_code": status_code,
                "status_message": getattr(error, "title", name),
                "error_message": error_message,
                "debug": traceback.format_exc(),
            },
            status=status_code,
        )
