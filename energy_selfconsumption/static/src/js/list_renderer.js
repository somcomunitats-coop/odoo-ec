/** @odoo-module **/

import {ListRenderer} from "@web/views/list/list_renderer";
import {listView} from "@web/views/list/list_view";
import {X2ManyField} from "@web/views/fields/x2many/x2many_field";
import {registry} from "@web/core/registry";

// Extender ListRenderer para personalizar el renderizado
class ListRendererDistributionTable extends ListRenderer {
  setup() {
    super.setup();
    this.distribution_table_type = "fixed";

    const context = this.props.list.model.rootParams.context;
    if (context && context.distribution_table_type) {
      this.distribution_table_type = context.distribution_table_type;
    }
  }

  // Personalización de las celdas de la tabla
  getFormattedValue(column, record) {
    if (this.distribution_table_type === "hourly" && column.name === "coefficient") {
      return "*";
    }
    return super.getFormattedValue(column, record);
  }
}

// Extender ListView para utilizar el ListRenderer personalizado
export const DistributionTableView = listView;
DistributionTableView.Renderer = ListRendererDistributionTable;

// Registrar el nuevo tipo de vista
registry.category("views").add("distribution_table", DistributionTableView);

// Extender X2ManyField para utilizar el ListRenderer personalizado
class ListRendererDistributionTableX2ManyField extends X2ManyField {
  setup() {
    super.setup();
    if (
      this.viewMode == "list" &&
      this.__owl__.parent.props.record.data["type"] == "hourly"
    ) {
      this.props.value.records.map((record) => {
        if ("coefficient" in record.data) {
          record.data["coefficient"] = "*";
          record.fields["coefficient"].type = "char";
        }
      });
    }
  }
}

// Registrar el nuevo tipo de X2ManyField
registry
  .category("fields")
  .add("distribution_table_one2many", ListRendererDistributionTableX2ManyField);
