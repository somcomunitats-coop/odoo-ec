/**
 * Inscription Data Website Handler
 * ================================
 *
 * This module handles dynamic form behavior for energy self-consumption inscription
 * forms on the website. It manages form field visibility, validation, and user
 * interactions for supply point owner data and privacy policy acceptance.
 *
 * Features:
 * - Dynamic form field visibility based on user selections
 * - Automatic form validation state management
 * - Privacy policy text toggle functionality
 * - Input formatting for contracted power fields
 * - Owner data conditional display
 *
 * Dependencies:
 * - jQuery for DOM manipulation
 * - oe_website_data for date picker and form utilities
 */

var oe_inscription_website_data = {
  /**
   * Initialize inscription form handlers
   * Sets up all event listeners and form behaviors
   */
  start: function () {
    $(".oe_website_data").each(function () {
      // Initialize date picker components
      oe_website_data.OnDatePicker(".o_website_form_date", ".o_website_form_date_past");

      // Initialize disabled form groups
      oe_website_data.onGroupDisable(".form-group-disabled");

      // ========================================
      // SUPPLY POINT OWNER DATA HANDLER
      // ========================================

      /**
       * Handle supply point owner data visibility
       * Shows/hides owner fields based on "same as member" selection
       */
      $("#supplypoint_owner_id_same").on("change", function (e) {
        if ($(e.target).val() == "yes") {
          // Hide owner data fields when same as member
          $(".owner_data").addClass("d-none");

          // Remove required validation for hidden fields
          $("#supplypoint_owner_id_name").prop("required", false);
          $("#supplypoint_owner_id_lastname").prop("required", false);
          $("#supplypoint_owner_id_gender").prop("required", false);
          $("#supplypoint_owner_id_birthdate_date").prop("required", false);
          $("#supplypoint_owner_id_phone").prop("required", false);
          $("#supplypoint_owner_id_lang").prop("required", false);
          $("#supplypoint_owner_id_vat").prop("required", false);
          $("#supplypoint_owner_id_email").prop("required", false);
          $("#supplypoint_owner_id_email_confirm").prop("required", false);
        } else {
          // Show owner data fields when different from member
          $(".owner_data").removeClass("d-none");

          // Add required validation for visible fields
          $("#supplypoint_owner_id_name").prop("required", true);
          $("#supplypoint_owner_id_lastname").prop("required", true);
          $("#supplypoint_owner_id_gender").prop("required", true);
          $("#supplypoint_owner_id_birthdate_date").prop("required", true);
          $("#supplypoint_owner_id_phone").prop("required", true);
          $("#supplypoint_owner_id_lang").prop("required", true);
          $("#supplypoint_owner_id_vat").prop("required", true);
          $("#supplypoint_owner_id_email").prop("required", true);
          $("#supplypoint_owner_id_email_confirm").prop("required", true);
        }
      });

      // ========================================
      // PRIVACY POLICY HANDLER
      // ========================================

      /**
       * Handle privacy policy text visibility toggle
       * Shows/hides the full privacy policy text
       */
      $("#project_conf_policy_privacy_text_click").on("click", function (e) {
        if ($("#project_conf_policy_privacy_text").hasClass("d-none")) {
          $("#project_conf_policy_privacy_text").removeClass("d-none");
        } else {
          $("#project_conf_policy_privacy_text").addClass("d-none");
        }
      });

      // ========================================
      // CONTRACTED POWER INPUT FORMATTER
      // ========================================

      /**
       * Format contracted power input to allow only numeric values with decimals
       * Ensures proper decimal formatting and prevents invalid characters
       */
      $("#supplypoint_contracted_power").on("input", function () {
        let value = $(this).val();

        // Remove all non-numeric characters except comma and dot
        value = value.replace(/[^0-9.,]/g, "");

        // Replace comma with dot for decimal consistency
        value = value.replace(",", ".");

        // Handle multiple decimal points
        let parts = value.split(".");
        if (parts.length > 2) {
          value = parts[0] + "." + parts.slice(1).join("");
        }

        $(this).val(value);
      });

      // ========================================
      // FORM INITIALIZATION
      // ========================================

      // Trigger initial state for privacy policy (collapsed by default)
      $("#project_conf_policy_privacy_text_click").trigger("click");

      // Trigger initial state for owner data visibility
      $("#supplypoint_owner_id_same").trigger("change");

      // Trigger any data-dependent form elements
      $(".data-trigger").trigger("change");
    });
  },
};

/**
 * Document ready handler
 * Initializes the inscription form when DOM is loaded
 */
$(document).ready(function () {
  oe_inscription_website_data.start();
});
