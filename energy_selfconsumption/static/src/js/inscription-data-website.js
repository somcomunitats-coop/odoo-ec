var oe_inscription_website_data = {
  start: function () {
    $(".oe_website_data").each(function () {
      oe_website_data.OnDatePicker(".o_website_form_date", ".o_website_form_date_past");

      oe_website_data.onGroupDisable(".form-group-disabled");

      $("#supplypoint_owner_id_same").on("change", function (e) {
        if ($(e.target).val() == "yes") {
          $(".owner_data").addClass("d-none");
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
          $(".owner_data").removeClass("d-none");
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
      $("#project_conf_policy_privacy_text_click").on("click", function (e) {
        if ($("#project_conf_policy_privacy_text").hasClass("d-none")) {
          $("#project_conf_policy_privacy_text").removeClass("d-none");
        } else {
          $("#project_conf_policy_privacy_text").addClass("d-none");
        }
      });
      $("#project_conf_policy_privacy_text_click").trigger("click");
      $("#supplypoint_owner_id_same").trigger("change");
      $(".data-trigger").trigger("change");
      $("#supplypoint_contracted_power").on("input", function () {
        let value = $(this).val();
        value = value.replace(/[^0-9.,]/g, "");
        value = value.replace(",", ".");
        let parts = value.split(".");
        if (parts.length > 2) {
          value = parts[0] + "." + parts.slice(1).join("");
        }
        $(this).val(value);
      });
    });
  },
};

$(document).ready(function () {
  oe_inscription_website_data.start();
});
