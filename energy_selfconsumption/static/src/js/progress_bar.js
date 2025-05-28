/**
 * Progress Bar Widget for Energy Self-consumption
 * ===============================================
 *
 * This module provides a custom progress bar widget for displaying power distribution
 * progress in energy self-consumption projects. The widget shows current vs maximum
 * distributed power with visual indicators for different states.
 *
 * Features:
 * - Dynamic progress calculation based on distributed vs max power
 * - Color-coded states (normal, complete, exceeded)
 * - Real-time percentage display
 * - Responsive styling with proper visual feedback
 *
 * @odoo-module
 */

import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";

/**
 * Progress Bar Widget Component
 *
 * Displays a visual progress bar for power distribution tracking.
 * Automatically calculates percentage and applies appropriate styling
 * based on current vs maximum values.
 */
class ProgressBarWidget extends Component {
  /**
   * Component setup and state initialization
   * Configures the widget state based on record data
   */
  setup() {
    // Extract values from component props
    const {record} = this.props;

    // Initialize component state using OWL hooks
    this.state = useState({
      max_quantity: record.data["max_distributed_power"] || 100,
      extra_label: "kW",
      current_quantity: record.data["distributed_power"] || 0,
    });

    // Calculate percentage based on current values
    this.state.percentage =
      (this.state.current_quantity / this.state.max_quantity) * 100;
  }

  /**
   * Get progress bar styling based on current percentage
   *
   * @returns {string} CSS style string for progress bar
   */
  get progressStyle() {
    let background_color = "#7C7BAD"; // Default purple color

    // Determine color based on progress state
    if (this.state.percentage > 100) {
      background_color = "#a10000"; // Red for exceeded
    } else if (this.state.percentage == 100) {
      background_color = "#00a12a"; // Green for complete
    }

    // Cap width at 100% even if percentage exceeds
    let width = this.state.percentage > 100 ? 100 : this.state.percentage;

    return `
            width: ${width}%;
            height: 100%;
            background-color: ${background_color};
        `;
  }

  /**
   * Get container styling for progress bar wrapper
   *
   * @returns {string} CSS style string for container
   */
  get containerStyle() {
    return `
            position: relative;
            height: 25px;
            background-color: #f5f5f5;
            border-radius: 4px;
            border: 1px solid #ccc;
        `;
  }

  /**
   * Get overlay styling for visual effects
   *
   * @returns {string} CSS style string for overlay
   */
  get overlayStyle() {
    return `
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: #adb5bd;
            opacity: 0.3;
        `;
  }
}

// Configure widget template
ProgressBarWidget.template = "ProgressBarWidgetTemplate";

// Register the widget in the field registry
registry.category("fields").add("progress_bar_widget", ProgressBarWidget);

export default ProgressBarWidget;
