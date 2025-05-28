/**
 * Distribution Table List Renderer
 * ================================
 *
 * This module provides custom list rendering functionality for distribution tables
 * in energy self-consumption projects. It extends the standard Odoo list view
 * to handle special display requirements for different distribution table types.
 *
 * Features:
 * - Custom rendering for hourly vs fixed distribution tables
 * - Dynamic coefficient display based on table type
 * - Extended X2Many field handling for distribution tables
 * - Context-aware rendering based on distribution table type
 *
 * Components:
 * - ListRendererDistributionTable: Custom list renderer
 * - DistributionTableView: Extended list view
 * - ListRendererDistributionTableX2ManyField: Custom X2Many field
 *
 * @odoo-module
 */

import {ListRenderer} from "@web/views/list/list_renderer";
import {listView} from "@web/views/list/list_view";
import {X2ManyField} from "@web/views/fields/x2many/x2many_field";
import {registry} from "@web/core/registry";

// ========================================
// CUSTOM LIST RENDERER
// ========================================

/**
 * Extended ListRenderer for Distribution Tables
 *
 * Provides custom rendering logic for distribution table lists,
 * handling different display modes based on table type (fixed vs hourly).
 */
class ListRendererDistributionTable extends ListRenderer {
  /**
   * Component setup and configuration
   * Initializes distribution table type from context
   */
  setup() {
    super.setup();
    this.distribution_table_type = "fixed";

    // Extract distribution table type from context
    const context = this.props.list.model.rootParams.context;
    if (context && context.distribution_table_type) {
      this.distribution_table_type = context.distribution_table_type;
    }
  }

  /**
   * Custom cell value formatting for distribution tables
   *
   * @param {Object} column - Column configuration object
   * @param {Object} record - Record data object
   * @returns {string} Formatted value for display
   */
  getFormattedValue(column, record) {
    // Special handling for coefficient column in hourly tables
    if (this.distribution_table_type === "hourly" && column.name === "coefficient") {
      return "*"; // Display asterisk for hourly coefficients
    }

    // Use default formatting for all other cases
    return super.getFormattedValue(column, record);
  }
}

// ========================================
// CUSTOM LIST VIEW
// ========================================

/**
 * Extended ListView for Distribution Tables
 * Uses the custom ListRenderer for specialized rendering
 */
export const DistributionTableView = listView;
DistributionTableView.Renderer = ListRendererDistributionTable;

// Register the custom view in the registry
registry.category("views").add("distribution_table", DistributionTableView);

// ========================================
// CUSTOM X2MANY FIELD
// ========================================

/**
 * Extended X2ManyField for Distribution Tables
 *
 * Provides custom handling for X2Many relationships in distribution tables,
 * specifically for coefficient display in hourly distribution types.
 */
class ListRendererDistributionTableX2ManyField extends X2ManyField {
  /**
   * Component setup and data transformation
   * Modifies coefficient field display for hourly distribution tables
   */
  setup() {
    super.setup();

    // Handle hourly distribution table coefficient display
    if (
      this.viewMode == "list" &&
      this.__owl__.parent.props.record.data["type"] == "hourly"
    ) {
      // Transform coefficient values for hourly tables
      this.props.value.records.map((record) => {
        if ("coefficient" in record.data) {
          // Replace coefficient value with asterisk
          record.data["coefficient"] = "*";
          // Change field type to char for proper display
          record.fields["coefficient"].type = "char";
        }
      });
    }
  }
}

// Register the custom X2Many field in the registry
registry
  .category("fields")
  .add("distribution_table_one2many", ListRendererDistributionTableX2ManyField);
