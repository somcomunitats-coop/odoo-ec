odoo.define("energy_selfconsumption.oe_inscription_data", ["energy_communities.oe_website_data"], function (require) {
  "use strict";

  var oe_website_data = require("energy_communities.oe_website_data");

  var oe_inscription_website_data = {
      start: function (){
        $(".oe_website_data").each(function () {
          var oe_inscription_website_data = this;

          oe_website_data.OnDatePicker(".o_website_form_date",".o_website_form_date_past");

          oe_website_data.onGroupDisable(".form-group-disabled");

          $("#supplypoint_owner_id_same").on("change", function (e) {
            if ( $(e.target).val() == "yes" ){
                $(".owner_data").addClass("d-none");
            }else{
                $(".owner_data").removeClass("d-none");
            }
          });

          $(".data-trigger").trigger("change");
        });
      },
  };

  $(document).ready(function () {
       oe_inscription_website_data.start();
  });

  return oe_website_data;
});
