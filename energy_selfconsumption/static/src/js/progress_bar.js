/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";

class ProgressBarWidget extends Component {
  setup() {
    // Obtener valores desde this.props
    const {record} = this.props;

    // Configurar el estado inicial usando hooks de OWL
    this.state = useState({
      max_quantity: record.data["max_distributed_power"] || 100,
      extra_label: "kW",
      current_quantity: record.data["distributed_power"] || 0,
    });

    // Calcular el porcentaje basado en los valores actuales
    this.state.percentage = Math.min(
      (this.state.current_quantity / this.state.max_quantity) * 100,
      100
    );
  }

  get progressStyle() {
    return `
      width: ${this.state.percentage}%;
      height: 100%;
      background-color: #7C7BAD;
    `;
  }

  get containerStyle() {
    return `
      position: relative;
      height: 25px;
      background-color: #f5f5f5;
      border-radius: 4px;
      border: 1px solid #ccc;
    `;
  }

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

ProgressBarWidget.template = "ProgressBarWidgetTemplate";
//ProgressBarWidget.props = ["options"];

// Register the widget in the field registry
registry.category("fields").add("progress_bar_widget", ProgressBarWidget);

export default ProgressBarWidget;
