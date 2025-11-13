odoo.define("cooperator.oe_cooperator_inherit", function (require) {
  "use strict";
  $(document).ready(function () {
    $(".oe_cooperator").each(function () {
      var oe_cooperator = this;

      $("#total_parts").change(function (event) {
        $("#share_price_span").html($(this).val());
        return false;
      });

      // We execute again the change method to take into consideration if the form has been already submitted
      $(oe_cooperator).on("change", "#ordered_parts", function (event) {
        var $share_price = $("#share_price").text();
        var $link = $(event.currentTarget);
        var quantity = $link[0].value;
        var total_part = quantity * $share_price;
        $("#total_parts").val(total_part);

        var $ordered_parts = $("#ordered_parts");
        // This block of code will grab submission value to take it into consideration
        if ($ordered_parts.data("submission_value")) {
          $ordered_parts.val($ordered_parts.data("submission_value"));
          $ordered_parts.data("submission_value", null);
        }
        $("#total_parts").change();
        return false;
      });
    });
  });
});
