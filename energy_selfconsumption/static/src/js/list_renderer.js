odoo.define("energy_selfconsumption.ListRenderer", function (require) {
  "use strict";

  var ListRenderer = require("web.ListRenderer");
  var ListView = require("web.ListView");
  var view_registry = require("web.view_registry");
  var FieldOne2Many = require("web.relational_fields").FieldOne2Many;
  var fieldRegistry = require("web.field_registry");

  var ListRendererDistributionTable = ListRenderer.extend({
    init: function (parent, state, params) {
      this._super.apply(this, arguments);
      this.distribution_table_type = "fixed";
      if (typeof this.state.getContext().distribution_table_type != "undefined") {
        this.distribution_table_type = this.state.getContext().distribution_table_type;
      }
    },

    _renderBodyCell: function (record, node, colIndex, options) {
      var $td = this._super.apply(this, arguments);
      if (
        this.distribution_table_type == "hourly" &&
        node.attrs["name"] == "coefficient"
      ) {
        $td.html("*");
      }
      return $td;
    },
  });

  var DistributionTableView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
      Renderer: ListRendererDistributionTable,
    }),
  });

  view_registry.add("distribution_table", DistributionTableView);

  var ListRendererDistributionTableFieldOne2Many = FieldOne2Many.extend({
    _getRenderer: function () {
      if (this.view.arch.tag === "tree") {
        return ListRendererDistributionTable;
      }
      return this._super.apply(this, arguments);
    },
  });

  fieldRegistry.add(
    "distribution_table_one2many",
    ListRendererDistributionTableFieldOne2Many
  );

  return ListRendererDistributionTable;
});
