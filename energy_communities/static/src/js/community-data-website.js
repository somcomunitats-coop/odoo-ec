odoo.define("community_data.oe_community_data", function (require) {
  "use strict";
  $(document).ready(function () {
    var ajax = require("web.ajax");

    $(".oe_community_data").each(function () {
      var oe_community_data = this;

      var locale = $(".o_website_form_date").data("locale");

      $.datepicker.regional = {
        ca_ES: {
          monthNamesShort: [
            "Gen",
            "Feb",
            "Mar",
            "Abr",
            "Mai",
            "Jun",
            "Jul",
            "Ago",
            "Set",
            "Oct",
            "Nov",
            "Dec",
          ],
        },
        es_ES: {
          monthNamesShort: [
            "Ene",
            "Feb",
            "Mar",
            "Abr",
            "May",
            "Jun",
            "Jul",
            "Ago",
            "Sept",
            "Oct",
            "Nov",
            "Dic",
          ],
        },
      };

      $.datepicker.setDefaults($.datepicker.regional[locale]);

      $(".o_website_form_date_past").datepicker({
        dateFormat: "dd/mm/yy",
        changeMonth: true,
        changeYear: true,
        maxDate: "today",
        yearRange: "2010:+0",
      });
      //$(oe_cooperator).on("change", "#ordered_parts", function (event) {
      //    var $share_price = $("#share_price").text();
      //    var $link = $(event.currentTarget);
      //    var quantity = $link[0].value;
      //    var total_part = quantity * $share_price;
      //    $("#total_parts").val(total_part);
      //    return false;
      //});

      //$(oe_cooperator).on("focusout", "input.js_quantity", function () {
      //    $("a.js_add_cart_json").trigger("click");
      //});

      //$("#share_product_id").trigger("change");
    });
  });
});
