import logging
import re

from odoo import _, http
from odoo.http import request

from odoo.addons.energy_communities.controllers.website_form_controllers import (
    WebsiteFormController,
)
from odoo.addons.energy_communities.utils import get_translation

# Constants for inscriptions form controller
DATE_PATTERN_REGEX = r"^\d{2}/\d{2}/\d{4}$"
FORM_CHECKBOX_ON_VALUE = "on"
FORM_CHECKBOX_OFF_VALUE = "off"
OWNER_SAME_YES = "yes"
OWNER_SAME_NO = "no"
DEFAULT_LANG_MODULE = "energy_communities_crm"
DEFAULT_LANG_CODE = "en"
LANG_CODE_SLICE_END = -3

# Gender options constants
GENDER_MALE = "male"
GENDER_FEMALE = "female"
GENDER_OTHER = "other"
GENDER_NOT_BINARY = "not_binary"
GENDER_NOT_SHARE = "not_share"

# Vulnerability situation options
VULNERABILITY_YES = "yes"
VULNERABILITY_NO = "no"

# Self-consumption options
SELFCONSUMPTION_YES = "yes"
SELFCONSUMPTION_NO = "no"

logger = logging.getLogger(__name__)


class WebsiteInscriptionsFormController(WebsiteFormController):
    """
    Website Inscriptions Form Controller

    This controller handles the public website form for energy self-consumption
    project inscriptions, including:
    - Form display and validation
    - Partner and supply point data collection
    - Inscription creation and processing
    - Email notifications
    - Multi-language support

    Features:
    - Public form access with validation
    - Comprehensive data validation
    - Partner verification and enrollment checks
    - Supply point owner management
    - Bank details and mandate handling
    - Email confirmation system
    """

    # Route definitions
    @http.route(
        ["/page/inscription-data", "/inscription-data"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def display_inscription_data_page(self, **kwargs):
        """
        Display inscription data page

        Main route for displaying the inscription form page with all
        necessary data and validation.

        Args:
            **kwargs: Request parameters

        Returns:
            http.Response: Rendered inscription form page
        """
        try:
            return self.display_data_page(kwargs, self.get_form_submit(kwargs), "id")
        except Exception as e:
            logger.error(f"Error displaying inscription data page: {e}")
            return request.render("website.404")

    @http.route(
        ["/inscription-data/submit"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def inscription_data_submit(self, **kwargs):
        """
        Handle inscription data submission

        Processes the submitted inscription form data, validates it,
        and creates the inscription record.

        Args:
            **kwargs: Form submission data

        Returns:
            http.Response: Success page or form with errors
        """
        try:
            return self.data_submit("id", kwargs)
        except Exception as e:
            logger.error(f"Error processing inscription submission: {e}")
            return request.render("website.404")

    # Model configuration methods
    def get_model_name(self):
        """
        Get the model name for this form controller

        Returns:
            str: Model name for self-consumption projects
        """
        return "energy_selfconsumption.selfconsumption"

    # Validation methods
    def data_validation_custom(self, model, values):
        """
        Custom validation for form display

        Validates that the project is active and accepting inscriptions
        before displaying the form.

        Args:
            model: Self-consumption project model
            values: Form values

        Returns:
            dict: Validation result with errors if any
        """
        try:
            if model.conf_state == "inactive":
                return {
                    "error_msgs": [
                        _(
                            "The form is not open. For more information write to your Energy Community {email}"
                        ).format(
                            email=model.company_id.email or _("(email not available)")
                        )
                    ],
                    "global_error": True,
                }

            return super().data_validation_custom(model, values)

        except Exception as e:
            logger.error(f"Error in data validation: {e}")
            return {
                "error_msgs": [
                    _("An error occurred during validation. Please try again.")
                ],
                "global_error": True,
            }

    def form_submit_validation(self, values):
        """
        Comprehensive form submission validation

        Validates all form data including partner verification, participation
        validation, and data format checks.

        Args:
            values: Form submission values

        Returns:
            dict: Validation result or validated values
        """
        try:
            # Validate privacy policy acceptance for different owners
            privacy_validation = self._validate_privacy_policy(values)
            if privacy_validation:
                return privacy_validation

            # Validate partner existence and membership
            partner_validation = self._validate_partner(values)
            if partner_validation:
                return partner_validation

            # Check for existing inscription
            inscription_validation = self._validate_existing_inscription(values)
            if inscription_validation:
                return inscription_validation

            # Validate email confirmation
            email_validation = self._validate_email_confirmation(values)
            if email_validation:
                return email_validation

            # Validate participation
            participation_validation = self._validate_participation(values)
            if participation_validation:
                return participation_validation

            # Validate owner-specific data if different from partner
            owner_validation = self._validate_owner_data(values)
            if owner_validation:
                return owner_validation

            return values

        except Exception as e:
            logger.error(f"Error in form submission validation: {e}")
            return {
                "error_msgs": [
                    _("An error occurred during validation. Please try again.")
                ],
                "global_error": True,
            }

    def _validate_privacy_policy(self, values):
        """
        Validate privacy policy acceptance

        Args:
            values: Form values

        Returns:
            dict: Error dict if validation fails, None if valid
        """
        if values.get("supplypoint_owner_id_same", OWNER_SAME_YES) == OWNER_SAME_NO:
            if (
                values.get("inscription_project_privacy", FORM_CHECKBOX_OFF_VALUE)
                != FORM_CHECKBOX_ON_VALUE
            ):
                return {
                    "error_msgs": [_("You must accept the privacy policy.")],
                    "global_error": True,
                }
        return None

    def _validate_partner(self, values):
        """
        Validate partner existence and membership

        Args:
            values: Form values

        Returns:
            dict: Error dict if validation fails, None if valid
        """
        try:
            project = self._get_project_from_values(values)
            partner = self._get_partner_from_values(values, project)

            if not partner:
                return {
                    "error_msgs": [_("Partner does not exist.")],
                    "global_error": True,
                }

            # Check membership requirements
            membership_validation = self._validate_partner_membership(partner, project)
            if membership_validation:
                return membership_validation

            return None

        except Exception as e:
            logger.error(f"Error validating partner: {e}")
            return {
                "error_msgs": [_("Error validating partner information.")],
                "global_error": True,
            }

    def _validate_partner_membership(self, partner, project):
        """
        Validate partner membership requirements

        Args:
            partner: Partner record
            project: Project record

        Returns:
            dict: Error dict if validation fails, None if valid
        """
        partner_with_type = partner.get_partner_with_type()

        if not partner_with_type.with_company(
            project.company_id.id
        ).no_member_autorized_in_energy_actions:
            cooperator = (
                request.env["cooperative.membership"]
                .sudo()
                .search(
                    [
                        ("company_id", "=", project.company_id.id),
                        ("partner_id", "=", partner_with_type.id),
                        ("cooperator", "=", True),
                        ("member", "=", True),
                    ]
                )
            )

            if not cooperator:
                return {
                    "error_msgs": [_("Partner is not a cooperator.")],
                    "global_error": True,
                }

        return None

    def _validate_existing_inscription(self, values):
        """
        Check for existing inscription

        Args:
            values: Form values

        Returns:
            dict: Error dict if inscription exists, None if valid
        """
        try:
            project = self._get_project_from_values(values)
            partner = self._get_partner_from_values(values, project)

            if partner:
                inscription = (
                    request.env["energy_selfconsumption.inscription_selfconsumption"]
                    .sudo()
                    .search(
                        [
                            ("project_id", "=", int(values["model_id"])),
                            ("partner_id", "=", partner.id),
                            ("code", "=", values["supplypoint_cups"]),
                        ]
                    )
                )

                if inscription:
                    return {
                        "error_msgs": [
                            _(
                                "You are already enrolled in this self-consumption project."
                            )
                        ],
                        "global_error": True,
                    }

            return None

        except Exception as e:
            logger.error(f"Error checking existing inscription: {e}")
            return {
                "error_msgs": [_("Error checking existing inscriptions.")],
                "global_error": True,
            }

    def _validate_email_confirmation(self, values):
        """
        Validate email confirmation match

        Args:
            values: Form values

        Returns:
            dict: Error dict if emails don't match, None if valid
        """
        email = values.get("supplypoint_owner_id_email", "")
        email_confirm = values.get("supplypoint_owner_id_email_confirm", "")

        if email != email_confirm:
            return {
                "error_msgs": [_("The email addresses do not match.")],
                "global_error": True,
            }

        return None

    def _validate_participation(self, values):
        """
        Validate participation existence

        Args:
            values: Form values

        Returns:
            dict: Error dict if participation invalid, None if valid
        """
        try:
            participation_quantity = float(
                values["inscriptionselfconsumption_participation"]
            )
            participation = (
                request.env["energy_selfconsumptions.participation"]
                .sudo()
                .search(
                    [
                        ("quantity", "=", participation_quantity),
                        ("project_id", "=", int(values["model_id"])),
                    ]
                )
            )

            if not participation:
                return {
                    "error_msgs": [_("Selected participation does not exist.")],
                    "global_error": True,
                }

            return None

        except (ValueError, TypeError):
            return {
                "error_msgs": [_("Invalid participation value.")],
                "global_error": True,
            }

    def _validate_owner_data(self, values):
        """
        Validate owner-specific data when different from partner

        Args:
            values: Form values

        Returns:
            dict: Error dict if validation fails, None if valid
        """
        if values.get("supplypoint_owner_id_same") == OWNER_SAME_NO:
            # Validate date format
            date_validation = self._validate_birthdate_format(values)
            if date_validation:
                return date_validation

            # Validate language
            language_validation = self._validate_language(values)
            if language_validation:
                return language_validation

            # Validate same partner as owner
            same_partner_validation = self._validate_same_partner_as_owner(values)
            if same_partner_validation:
                return same_partner_validation

        return None

    def _validate_birthdate_format(self, values):
        """
        Validate birthdate format

        Args:
            values: Form values

        Returns:
            dict: Error dict if format invalid, None if valid
        """
        birthdate = values.get("supplypoint_owner_id_birthdate_date", "")
        date_pattern = re.compile(DATE_PATTERN_REGEX)

        if not date_pattern.match(birthdate):
            return {
                "error_msgs": [_("Invalid date format. Please use DD/MM/YYYY format.")],
                "global_error": True,
            }

        return None

    def _validate_language(self, values):
        """
        Validate language selection

        Args:
            values: Form values

        Returns:
            dict: Error dict if language invalid, None if valid
        """
        language_code = values.get("supplypoint_owner_id_lang", "")

        if language_code:
            lang = (
                request.env["res.lang"]
                .sudo()
                .search(
                    [
                        "|",
                        "|",
                        ("name", "=", language_code),
                        ("code", "=", language_code),
                        ("iso_code", "=", language_code),
                    ]
                )
            )

            if not lang:
                return {
                    "error_msgs": [_("Selected language not found.")],
                    "global_error": True,
                }

        return None

    def _validate_same_partner_as_owner(self, values):
        """
        Validate same partner as owner
        """
        if values.get("supplypoint_owner_id_same") == OWNER_SAME_NO:
            if values.get("inscription_partner_id_vat") == values.get(
                "supplypoint_owner_id_vat"
            ):
                return {
                    "error_msgs": [
                        _(
                            "You have selected ‘No’ to the question ‘The holder is the same partner’, in this case the NIF/CIF of the Holder cannot coincide with that of the partner."
                        )
                    ],
                    "global_error": True,
                }
        return None

    # Helper methods for validation
    def _get_project_from_values(self, values):
        """
        Get project record from form values

        Args:
            values: Form values

        Returns:
            project: Self-consumption project record
        """
        return (
            request.env["energy_selfconsumption.selfconsumption"]
            .sudo()
            .browse(int(values["model_id"]))
        )

    def _get_partner_from_values(self, values, project):
        """
        Get partner record from form values

        Args:
            values: Form values
            project: Project record

        Returns:
            partner: Partner record or None
        """
        return (
            request.env["res.partner"]
            .sudo()
            .search(
                [
                    ("vat", "=", values["inscription_partner_id_vat"]),
                    ("parent_id", "=", False),
                    ("company_ids", "in", (project.company_id.id)),
                ]
            )
        )

    # Form field definitions and configuration
    def get_data_main_fields(self):
        """
        Get main form field definitions

        Returns:
            dict: Field definitions with labels
        """
        return {
            "company_name": _("Company Name"),
            "project_name": _("Energy Project Name"),
            "project_conf_used_in_selfconsumption": False,
            "project_conf_vulnerability_situation": False,
            "project_conf_bank_details": False,
            "project_header_description": _("Header description on website form"),
            "inscription_partner_id_vat": _("VAT of the partner"),
            "supplypoint_cups": _("CUPS"),
            "supplypoint_street": _("Address"),
            "supplypoint_city": _("City"),
            "supplypoint_zip": _("Zip"),
            "supplypoint_contracted_power": _("Maximum contracted power"),
            "supplypoint_cadastral_reference": _("Cadastral reference of the property"),
            "supplypoint_used_in_selfconsumption": _(
                "Do you currently have self-consumption?"
            ),
            "supplypoint_owner_id_same": _("Is the owner the same partner?"),
            "supplypoint_owner_id_name": _("Name"),
            "supplypoint_owner_id_lastname": _("Lastname"),
            "supplypoint_owner_id_gender": _("Gender"),
            "supplypoint_owner_id_birthdate_date": _("Birthdate"),
            "supplypoint_owner_id_phone": _("Phone"),
            "supplypoint_owner_id_lang": _("Language"),
            "supplypoint_owner_id_vat": _("CIF/NIF"),
            "supplypoint_owner_id_email": _("E-mail"),
            "supplypoint_owner_id_email_confirm": _("Confirm E-mail"),
            "supplypoint_owner_id_vulnerability_situation": _(
                "Are you in a vulnerable situation?"
            ),
            "project_conf_policy_privacy_text": _("Privacy policy file text"),
            "inscription_project_privacy": _("I accept privacy policy"),
            "inscriptionselfconsumption_annual_electricity_use": _(
                "Annual electricity use?"
            ),
            "inscriptionselfconsumption_participation": _(
                "What participation would you like?"
            ),
            "inscription_acc_number": _("IBAN"),
            "inscriptionselfconsumption_accept": _(
                "I accept and authorize being able to issue payments to this bank account as part of participation in this shared self-consumption project of my energy community"
            ),
        }

    def get_extra_data_main_fields(self, model, model_values):
        """
        Get extra data for form fields from model

        Args:
            model: Self-consumption project model
            model_values: Current model values

        Returns:
            dict: Updated model values with extra data
        """
        try:
            model_values.update(
                {
                    "company_name": model.company_id.name,
                    "project_name": model.name,
                    "model_id": model.id,
                    "project_model_key": "model_id",
                    "project_header_description": model.conf_header_description,
                    "project_conf_used_in_selfconsumption": model.conf_used_in_selfconsumption,
                    "project_conf_vulnerability_situation": model.conf_vulnerability_situation,
                    "project_conf_bank_details": model.conf_bank_details,
                    "project_conf_policy_privacy_text": model.company_id.data_policy_approval_text,
                }
            )

            return model_values

        except Exception as e:
            logger.error(f"Error getting extra data fields: {e}")
            return model_values

    def get_data_custom_submit(self, kwargs):
        """
        Get custom submission data

        Args:
            kwargs: Request arguments

        Returns:
            dict: Submission values
        """
        return kwargs

    # URL and form configuration methods
    def get_data_page_url(self, values):
        """
        Get data page URL

        Args:
            values: Form values

        Returns:
            str: Data page URL
        """
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/inscription-data?model_id={values['model_id']}"

    def get_form_submit(self, values):
        """
        Get form submit reference

        Args:
            values: Form values

        Returns:
            int: Form submit reference ID
        """
        return request.env.ref("energy_selfconsumption.inscription_data_page").id

    def get_form_submit_url(self, values):
        """
        Get form submit URL

        Args:
            values: Form values

        Returns:
            str: Form submit URL
        """
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/inscription-data/submit"

    def get_translate_field_label(self, source):
        """
        Get translated field label

        Args:
            source: Source field name

        Returns:
            str: Translated label
        """
        try:
            lang = DEFAULT_LANG_CODE
            if "lang" in request.env.context:
                lang = request.env.context["lang"][:LANG_CODE_SLICE_END]

            field_label = self.get_data_main_fields().get(source, source)
            return get_translation(field_label, lang, DEFAULT_LANG_MODULE)

        except Exception as e:
            logger.error(f"Error getting translated label for {source}: {e}")
            return source

    # Form options and choices
    def get_fill_values_custom(self, values):
        """
        Fill custom values for form options

        Args:
            values: Current form values

        Returns:
            dict: Updated values with options
        """
        try:
            # Add boolean choice options
            values.update(self._get_boolean_choice_options())

            # Add gender options
            values["supplypoint_owner_id_gender_options"] = self._get_gender_options()

            # Add participation options
            values[
                "inscriptionselfconsumption_participation_options"
            ] = self._get_participation_options(values)

            # Add language options
            values["supplypoint_owner_id_lang_options"] = self._get_language_options()

            # Add help text
            values.update(self._get_help_texts())

            return values

        except Exception as e:
            logger.error(f"Error filling custom values: {e}")
            return values

    def _get_boolean_choice_options(self):
        """
        Get boolean choice options for various fields

        Returns:
            dict: Boolean choice options
        """
        yes_no_options = [
            {"id": SELFCONSUMPTION_YES, "name": _("Yes")},
            {"id": SELFCONSUMPTION_NO, "name": _("No")},
        ]

        return {
            "supplypoint_used_in_selfconsumption_options": yes_no_options,
            "supplypoint_owner_id_same_options": yes_no_options,
            "supplypoint_owner_id_vulnerability_situation_options": yes_no_options,
        }

    def _get_gender_options(self):
        """
        Get gender selection options

        Returns:
            list: Gender options
        """
        return [
            {"id": GENDER_MALE, "name": _("Male")},
            {"id": GENDER_FEMALE, "name": _("Female")},
            {"id": GENDER_OTHER, "name": _("Other")},
            {"id": GENDER_NOT_BINARY, "name": _("Not binary")},
            {"id": GENDER_NOT_SHARE, "name": _("I prefer not to share")},
        ]

    def _get_participation_options(self, values):
        """
        Get participation options for the project

        Args:
            values: Form values

        Returns:
            list: Participation options
        """
        try:
            participations = (
                request.env["energy_selfconsumptions.participation"]
                .sudo()
                .search([("project_id", "=", int(values["model_id"]))])
            )

            return [
                {"id": participation.quantity, "name": participation.name}
                for participation in participations
            ]

        except Exception as e:
            logger.error(f"Error getting participation options: {e}")
            return []

    def _get_language_options(self):
        """
        Get language selection options

        Returns:
            list: Language options
        """
        try:
            langs = request.env["res.lang"].sudo().search([])
            return [{"id": lang.iso_code, "name": lang.name} for lang in langs]

        except Exception as e:
            logger.error(f"Error getting language options: {e}")
            return []

    def _get_help_texts(self):
        """
        Get help texts for form fields

        Returns:
            dict: Help texts
        """
        return {
            "supplypoint_cups_title": _(
                "CUPS is the Unified Code of the Point of Supply. "
                "You can find it on electricity bills."
            ),
            "supplypoint_cadastral_reference_title": _(
                "Information necessary for the formalization of the distribution agreement. "
                "You can find it at cadastro.es"
            ),
            "project_conf_used_in_selfconsumption_title": _(
                "Is there already an individual photovoltaic self-consumption or "
                "collective at this supply point?"
            ),
            "project_conf_vulnerability_situation_title": _(
                "Do you have a recognized situation of vulnerability due to energy poverty or "
                "other type of social support need?"
            ),
            "inscriptionselfconsumption_annual_electricity_use_title": _(
                "You can find the annual electricity use on the electricity bill "
                "(Total annual consumption). Put it in kWh/year"
            ),
            "inscriptionselfconsumption_participation_title": _(
                "How much power of the collective PV installation would you like to "
                "purchase."
            ),
        }

    # Form processing and inscription creation
    def process_metadata(self, model, values):
        """
        Process form metadata and create inscription

        Args:
            model: Self-consumption project model
            values: Form submission values

        Returns:
            dict: Processing result
        """
        try:
            # Validate bank details acceptance if required
            bank_validation = self._validate_bank_details_acceptance(model, values)
            if bank_validation:
                return bank_validation

            # Create inscription
            inscription_result = self._create_inscription(model, values)
            if inscription_result:
                return inscription_result

            # Send confirmation email
            self._send_confirmation_email(model, values)

            return values

        except Exception as e:
            logger.error(f"Error processing metadata: {e}")
            return {
                "error_msgs": [
                    _(
                        "An error occurred while processing your inscription. Please try again."
                    )
                ],
                "global_error": True,
            }

    def _validate_bank_details_acceptance(self, model, values):
        """
        Validate bank details acceptance if required

        Args:
            model: Project model
            values: Form values

        Returns:
            dict: Error dict if validation fails, None if valid
        """
        if model.conf_bank_details:
            if (
                values.get("inscriptionselfconsumption_accept")
                != FORM_CHECKBOX_ON_VALUE
            ):
                return {
                    "error_msgs": [
                        _(
                            "You must accept and authorize being able to issue payments to this bank account as part of participation in this shared self-consumption project of your energy community."
                        )
                    ],
                    "global_error": True,
                }
        return None

    def _create_inscription(self, model, values):
        """
        Create inscription record

        Args:
            model: Project model
            values: Form values

        Returns:
            dict: Error dict if creation fails, None if successful
        """
        try:
            error, message = (
                request.env["energy_selfconsumption.create_inscription_selfconsumption"]
                .sudo()
                .create_inscription(values, model)
            )

            if error:
                return {
                    "error_msgs": [message],
                    "global_error": True,
                }

            return None

        except Exception as e:
            logger.error(f"Error creating inscription: {e}")
            return {
                "error_msgs": [_("Error creating inscription. Please try again.")],
                "global_error": True,
            }

    def _send_confirmation_email(self, model, values):
        """
        Send confirmation email to partner

        Args:
            model: Project model
            values: Form values
        """
        try:
            partner = self._get_partner_from_values(values, model)
            if partner:
                self.send_email(model, partner)
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")

    def send_email(self, model, partner):
        """
        Send email notification to partner

        Args:
            model: Self-consumption project model
            partner: Partner record
        """
        try:
            if not partner.email:
                logger.warning(f"No email address for partner {partner.id}")
                return

            ctx = {
                "email_to": partner.email,
                "lang": partner.lang or "en_US",
                "partner_name": partner.name,
            }

            template = request.env.ref(
                "energy_selfconsumption.selfconsumption_insciption_form"
            ).sudo()
            template.with_context(ctx).send_mail(
                force_send=True,
                res_id=model.id,
                email_layout_xmlid="mail.mail_notification_layout",
            )

            logger.info(f"Confirmation email sent to partner {partner.id}")

        except Exception as e:
            logger.error(f"Error sending email to partner {partner.id}: {e}")

    # Utility methods
    def get_controller_info(self):
        """
        Get information about this controller

        Returns:
            dict: Controller information
        """
        return {
            "controller_name": "WebsiteInscriptionsFormController",
            "supported_routes": [
                "/page/inscription-data",
                "/inscription-data",
                "/inscription-data/submit",
            ],
            "authentication_required": False,
            "supported_methods": ["GET", "POST"],
            "model_name": self.get_model_name(),
        }
