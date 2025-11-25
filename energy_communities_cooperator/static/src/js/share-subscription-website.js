odoo.define(
  "energy_communities_cooperator.share_subscription_website",
  function (require) {
    "use strict";
    $(document).ready(function () {
      $("#share_product_id").change(function (event) {
        event.preventDefault();
        var payment_method = $("#share_product_id option:selected").data("extra_2");
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
          "extra"
        );
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
        } else {
          $("#transfer_text>#prodPrice").text(total_price);
        }
      });
      $("#payment_method").change(function (event) {
        event.preventDefault();
        var target = $(event.target);
        var payment_method = target.val();
        if (payment_method == "sepa") {
          $("#sepa_text").show();
          $("#transfer_text").hide();
          $("div[name='iban_container']").parent().show();
          $("div[name='conditions_payment_container']").parent().show();
        } else {
          $("#sepa_text").hide();
          $("#transfer_text").show();
          $("div[name='iban_container']").parent().hide();
          $("div[name='conditions_payment_container']").parent().hide();
          $("#iban").val("");
          $("#conditions_payment").val(false);
        }
        $("#ordered_parts").change();
      });

      $("#share_product_id").change();
    });
  }
);
