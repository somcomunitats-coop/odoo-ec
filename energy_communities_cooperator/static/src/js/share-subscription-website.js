odoo.define(
  "energy_communities_cooperator.share_subscription_website",
  function (require) {
    "use strict";
    $(document).ready(function () {
      $("#share_product_id").change(function (event) {
        event.preventDefault();
        var payment_method = $("#share_product_id option:selected").data(
          "payment-method"
        );
        $("#payment_method").val(payment_method);
        $("#ordered_parts").val(1);
        $("#ordered_parts").change();
        $("#payment_method").change();
      });
      $("#ordered_parts").change(function (event) {
        event.preventDefault();
        var target = $(event.target);
        var ordered_parts = target.val();
        var share_product_id_price = $("#share_product_id option:selected").data(
          "list-price"
        );
        var minimum_quantity = $("#share_product_id option:selected").data(
          "minimum-quantity"
        );
        if (ordered_parts < minimum_quantity) {
          ordered_parts = minimum_quantity;
          $("#ordered_parts").val(minimum_quantity);
        }
        if (!share_product_id_price) {
          share_product_id_price = 0;
        }
        $("#total_price").val(
          parseFloat(ordered_parts) * parseFloat(share_product_id_price)
        );
        $("#total_price").change();
      });
      $("#total_price").change(function (event) {
        event.preventDefault();
        var target = $(event.target);
        var total_price = target.val();
        if ($("#payment_method").val() == "sepa") {
          $("#sepa_text>#prodPrice").text(total_price);
          $("#sepa_text").show();
          $("#transfer_text").hide();
        } else {
          $("#transfer_text>#prodPrice").text(total_price);
          $("#sepa_text").hide();
          $("#transfer_text").show();
        }
        if (total_price == 0) {
          $("#sepa_text").hide();
          $("#transfer_text").hide();
        }
      });
      $("#payment_method").change(function (event) {
        event.preventDefault();
        var target = $(event.target);
        var payment_method = target.val();
        if (payment_method == "sepa") {
          $("div[name='iban_container']").parent().show();
          $("div[name='conditions_payment_container']").parent().show();
          $(".h3_company_bank_details").show();
          $("#iban").attr("required", true);
          $("#conditions_payment").attr("required", true);
        } else {
          $("div[name='iban_container']").parent().hide();
          $("div[name='conditions_payment_container']").parent().hide();
          $(".h3_company_bank_details").hide();
          $("#iban").val("");
          $("#iban").attr("required", false);
          $("#conditions_payment").val(false);
          $("#conditions_payment").attr("required", false);
        }
        $("#ordered_parts").change();
      });

      $("#share_product_id").change();

      $("form").on("submit", function (event) {
        event.preventDefault();
        var form = $(this);

        // Helper function to validate email confirmation
        function validateEmailConfirmation(
          emailField,
          confirmationField,
          errorMessage
        ) {
          var email = emailField.val();
          var emailConfirmation = confirmationField.val();

          // If both fields have values, they must match
          if (email && emailConfirmation) {
            if (email !== emailConfirmation) {
              alert(errorMessage);
              return false;
            }
          }
          // If one field has value but the other doesn't, it's an error
          else if ((email && !emailConfirmation) || (!email && emailConfirmation)) {
            alert(errorMessage);
            return false;
          }

          const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (email && !regex.test(email)) {
            alert("Email is not valid");
            return false;
          }
          if (emailConfirmation && !regex.test(emailConfirmation)) {
            alert("Email confirmation is not valid");
            return false;
          }

          return true;
        }

        // Validate email fields
        if (
          !validateEmailConfirmation(
            $("#email"),
            $("#email_confirmation"),
            "Email and email confirmation do not match"
          )
        ) {
          return false;
        }

        // Validate company email fields
        if (
          !validateEmailConfirmation(
            $("#company_email"),
            $("#company_email_confirmation"),
            "Company email and company email confirmation do not match"
          )
        ) {
          return false;
        }

        // If all validations pass, submit the form
        form.off("submit").submit();
      });
    });
  }
);
