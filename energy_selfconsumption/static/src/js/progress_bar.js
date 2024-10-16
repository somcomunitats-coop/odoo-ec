odoo.define("energy_selfconsumption.ProgressBarWidget", function (require) {
  "use strict";

  var AbstractField = require("web.AbstractField");
  var fieldRegistry = require("web.field_registry");

  var ProgressBarWidget = AbstractField.extend({
    supportedFieldTypes: ["float"], // You can use 'integer' or 'float' according to the data type

    init: function (parent, state, params) {
      this._super.apply(this, arguments);
      // Get field values
      this.max_quantity = this.record.data[this.attrs.options.max_quantity] || 100; // Maximum quantity
      this.extra_label = this.attrs.options.extra_label || ""; // Extra label
      this.current_quantity = this.value || 0; // Amount obtained
      this.percentage = Math.min(
        (this.current_quantity / this.max_quantity) * 100,
        100
      ); // Percentage
    },

    _render: function () {
      // Generate progress bars
      this.$el.html(`
                <div class="o_progress_bar">
                    <div class="progress-bar-container" style="position: relative; height: 25px; background-color: #f5f5f5; border-radius: 4px; border: 1px solid #ccc;">
                        <div class="progress-bar-green" style="width: ${
                          this.percentage
                        }%; height: 100%; background-color: #7C7BAD;"></div>
                        <div class="progress-bar-red" style="position: absolute; left: 0; top: 0; width: 100%; height: 100%; background-color: #adb5bd; opacity: 0.3;"></div>
                    </div>
                    <span>${this.percentage.toFixed(2)}%</span>
                    <span style="display: block;float: right;">${this.current_quantity.toFixed(
                      2
                    )} / ${this.max_quantity.toFixed(2)} ${this.extra_label}</span>
                </div>
            `);
    },
  });

  // Register the widget in the field record
  fieldRegistry.add("progress_bar_widget", ProgressBarWidget);

  return ProgressBarWidget;
});
