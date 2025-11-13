odoo.define("cooperator.oe_cooperator_inherit", function (require) {
  "use strict";
  $(document).ready(function () {
    var ajax = require("web.ajax");

    $(".oe_cooperator").each(function () {
      var oe_cooperator = this;

      $("#share_product_id").off("change");

      $("#share_product_id").change(function () {
        var share_product_id = $("#share_product_id").val();
        ajax
          .jsonRpc("/subscription/get_share_product", "call", {
            share_product_id: share_product_id,
          })
          .then(function (data) {
            $("#share_price").text(data[share_product_id].list_price);
            $("#ordered_parts").val(data[share_product_id].min_qty);
            if (data[share_product_id].force_min_qty === true) {
              $("#ordered_parts").data("min", data[share_product_id].min_qty);
            }
            $("#ordered_parts").change();
            var $share_price = $("#share_price").text();
            $('input[name="total_parts"]').val(
              $("#ordered_parts").val() * $share_price
            );
            $('input[name="total_parts"]').change();

            $(".col-xs-12.col-sm-10.col-md-8.col-lg-6 p>span")[0].textContent =
              $("#ordered_parts").val() * $share_price;
          });
      });

      $("#ordered_parts").off("change");
      // We execute again the change method to take into consideration if the form has been already submitted
      $(oe_cooperator).on("change", "#ordered_parts", function (event) {
        var $share_price = $("#share_price").text();
        var $ordered_parts = $("#ordered_parts");
        var $link = $(event.currentTarget);
        var quantity = $link[0].value;
        // This block of code will grab submission value to take it into consideration
        if ($ordered_parts.data("submission_value")) {
          $ordered_parts.val($ordered_parts.data("submission_value"));
          $ordered_parts.data("submission_value", null);
        }
        var total_part = quantity * $share_price;
        $("#total_parts").val(total_part);

        $(".col-xs-12.col-sm-10.col-md-8.col-lg-6 p>span")[0].textContent = total_part;
        return false;
      });
    });
  });
});
