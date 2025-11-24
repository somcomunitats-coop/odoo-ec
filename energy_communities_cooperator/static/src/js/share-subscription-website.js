odoo.define(
  "energy_communities_cooperator.share_subscription_website",
  function (require) {
    "use strict";
    $(document).ready(function () {
      $("#share_product_id").change(function (event) {
        event.preventDefault();
        // var target = $(event.target);
        // var share_product_id_price = target.data("data-extra");
        $("#ordered_parts").val(1);
        $("#ordered_parts").change();
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
        $("#prodPrice").text(total_price);
      });

      $("#share_product_id").change();
    });
  }
);
