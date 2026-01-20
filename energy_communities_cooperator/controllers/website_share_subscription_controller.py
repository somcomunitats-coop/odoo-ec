import logging

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
    STATUS_CODE_CONSISTENCY_ERROR,
    STATUS_CODE_SERVER_ERROR,
    _get_headline_fixed_sepa_message,
    _get_headline_fixed_transfer_message,
    _get_subscription_mode_headline_message,
    _get_subscription_mode_page_title_message,
)
from ..exceptions import (
    ComponentValidationError,
    ControllerContextValidationError,
    FormValidationError,
)
from ..schemas import (
    SubscriptionRequestCreationParams,
    WebsiteShareSubscriptionContext,
    WebsiteShareSubscriptionSubmissionBase,
    WebsiteShareSubscriptionSubmissionCompanyMember,
    WebsiteShareSubscriptionSubmissionVoluntary,
)
from ..utils import subscription_request_utils

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
            context_creation_params_dict = self._get_context_creation_params_dict(
                kwargs
            )
            ctx = WebsiteShareSubscriptionContext(**context_creation_params_dict)
        except ControllerContextValidationError as e:
            # Render error page if context validation fails
            return self._render_error_page(e)
        values = self._get_page_values(ctx)
        http_code = 200
        if request.httprequest.method == "POST":
            try:
                values = self._process_form(request, ctx)
            except FormValidationError as e:
                _logger.error(e.title)
                # now we return form with values pre-selected and error message on top
                if e.http_error_code == 500:
                    return self._render_error_page(e)
                http_code = e.http_error_code
                values["error"] = {"title": e.title, "messages": e.messages}
                self._populate_form_values_from_submission(request, values)
        return self._render_page(values, http_code)

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
        if isinstance(error, ComponentValidationError) or isinstance(
            error, FormValidationError
        ):
            error_message = ""
            for e in error.messages:
                error_message += e + "\n"
        else:
            error_message = error.message
        return request.render(
            "http_routing.http_error",
            {
                "status_code": error.http_error_code,
                "status_message": error.title,
                "error_message": error_message,
                "debug": "debug",
            },
            status=error.http_error_code,
        )

    def _populate_form_values_from_submission(self, request, values):
        form_submission = dict(request.httprequest.form)
        for field in values["form_fields"]:
            field_key = field.get("key")
            if field_key in form_submission:
                field["value"] = form_submission[field_key]

    def _process_form(self, request, ctx):
        """
        Process form submission data using SubscriptionRequestUtils component.

        Validates and creates subscription request from form data.

        Args:
            request: Dictionary containing form submission data and context
            ctx: WebsiteShareSubscriptionContext containig all context information
        """
        try:
            # Extract form data from request
            if ctx.subscription_mode.value == "voluntary":
                form_submission = WebsiteShareSubscriptionSubmissionVoluntary(
                    **dict(request.httprequest.form)
                )
            elif ctx.subscription_mode.value == "company_member":
                form_submission = WebsiteShareSubscriptionSubmissionCompanyMember(
                    **dict(request.httprequest.form)
                )
            else:
                form_submission = WebsiteShareSubscriptionSubmissionBase(
                    **dict(request.httprequest.form)
                )
        except PydanticValidationError as e:
            raise FormValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                MAPPING_FORM_ERROR_TITLE["general"],
                self._get_errors_arr(e),
            )
        try:
            creation_params = self._get_subscription_request_creation_params_dict(
                form_submission, ctx
            )
        except FormValidationError as e:
            raise e
        except Exception as ge:
            raise FormValidationError(
                STATUS_CODE_SERVER_ERROR,
                _("There is a problem preparing creation params for request."),
                [
                    ge.args[0],
                    _("Please contact the platform administrator to fix the issue."),
                ],
            )
        try:
            subscription_request_creation_params = SubscriptionRequestCreationParams(
                **creation_params
            )
        except PydanticValidationError as e:
            raise FormValidationError(
                STATUS_CODE_CONSISTENCY_ERROR,
                MAPPING_FORM_ERROR_TITLE["general"],
                self._get_errors_arr(e),
            )
        try:
            # Use component to validate and create subscription request
            with subscription_request_utils(request.env) as component:
                subscription_request = component.create_subscription_request(
                    subscription_request_creation_params
                )
        except ComponentValidationError as e:
            raise FormValidationError(e.http_error_code, e.title, e.messages)
        return self._get_page_base_values(ctx) | {
            "form_submitted": True,
            "success_msg": MAPPING_FORM_SUCCESS["general"],
        }

    def _get_errors_arr(self, e):
        e_msgs = []
        for error in e.errors():
            e_msgs.append(
                "{}: {} ({})".format(error["loc"][0], error["msg"], error["type"])
            )
        return e_msgs

    # getters
    def _get_context_creation_params_dict(self, kwargs):
        """
        Build dictionary of parameters needed to create WebsiteShareSubscriptionContext.

        Extracts and processes URL parameters to build context creation dictionary.
        Maps subscription mode to membership and member type modes, retrieves company
        and product category, and determines form type and available products.

        Args:
            kwargs: URL parameters from route

        Returns:
            Dictionary with all parameters needed for context creation
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
        return {
            "membership_mode": membership_mode,
            "membertype_mode": membertype_mode,
            "subscription_mode": subscription_mode,
            "formtype_mode": formtype_mode,
            "company": company,
            "product_categ": product_categ,
        } | self._get_page_products_dict(
            company, product_categ, query_product, formtype_mode, membertype_mode
        )

    def _get_subscription_request_creation_params_dict(self, form_submission, ctx):
        creation_params = form_submission.model_dump()
        creation_params["share_product_id"] = (
            request.env["product.template"]
            .sudo()
            .search([("id", "=", creation_params["share_product_id"])])
        )
        creation_params["product_categ"] = ctx.product_categ
        creation_params["company_id"] = ctx.company
        creation_params["membertype_mode"] = ctx.membertype_mode
        if ctx.subscription_mode.value == "voluntary":
            creation_params["vat"] = creation_params["vat"].strip().upper()
            partner = (
                request.env["res.partner"]
                .sudo()
                .get_cooperator_from_vat(creation_params["vat"], ctx.company.id)
            )
            # TODO: Must the person be a effective cooperator???
            if not partner:
                raise FormValidationError(
                    STATUS_CODE_CONSISTENCY_ERROR,
                    MAPPING_FORM_ERROR_TITLE["general"],
                    [_("We couldn't find a member for ")],
                )
            creation_params |= (
                self._get_subscription_request_creation_params_from_partner(partner)
            )
        else:  # memeber or company_member or invited or company_invites
            creation_params["country_id"] = (
                request.env["res.country"]
                .sudo()
                .search([("id", "=", creation_params["country_id"])])
            )
            lang_model = (
                request.env["res.lang"]
                .sudo()
                .search([("id", "=", creation_params["lang"])])
            )
            if lang_model:
                creation_params["lang"] = lang_model.code
            else:
                creation_params["lang"] = ""
        return creation_params

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
        if ctx.company.display_generic_rules_approval:
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_GENERIC_RULES["generic_rules"][
                "description"
            ] = ctx.company.generic_rules_approval_text
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_GENERIC_RULES["generic_rules"][
                "required"
            ] = ctx.company.generic_rules_approval_required
            form_fields |= MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_GENERIC_RULES
        if ctx.company.display_internal_rules_approval:
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_INTERNAL_RULES["internal_rules"][
                "description"
            ] = ctx.company.internal_rules_approval_text
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_INTERNAL_RULES["internal_rules"][
                "required"
            ] = ctx.company.internal_rules_approval_required
            form_fields |= MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_INTERNAL_RULES
        if ctx.company.display_financial_risk_approval:
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_FINANCIAL_RISK["financial_risk"][
                "description"
            ] = ctx.company.financial_risk_approval_text
            MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_FINANCIAL_RISK["financial_risk"][
                "required"
            ] = ctx.company.financial_risk_approval_required
            form_fields |= MAPPING__BASE__DEFAULT_FORM_FIELDS_VALUES_FINANCIAL_RISK
        if ctx.company.display_data_policy_approval:
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
            return ctx.share_product_id.html_specific_products
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
        if isinstance(path, bool):
            return path

        # Split path into keys
        keys = path.split(".")
        if len(keys) == 1:
            return ""

        # Navigate through nested structure
        current = data
        for key in keys:
            # Handle tuple values (selection fields return tuples)
            if isinstance(current, tuple):
                return current[1]

            # Convert recordset to dictionary if needed
            if not isinstance(current, dict):
                try:
                    current = current.read()[0]  # Convert the record to a dictionary
                except:
                    return ""  # Return an empty string if the record cannot be converted to a dictionary

            # Check if key exists in current dictionary
            if key not in current:
                return ""  # Return an empty string if the field is not found

            # Move to next level
            current = current[key]
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
