import base64
import re
from datetime import datetime

from odoo import _, http
from odoo.http import request

class WebsiteFormController(http.Controller):

    # Controlador principal para obtener los datos de renderizado del formulario
    def display_data_page(self, values, render_page, column_search, data_main_fields={}):
        response = self._page_render_validation(values, render_page, column_search)
        if response is not True:
            return response
        # prefill values
        model_values = self.get_values(values, column_search, data_main_fields)
        model_values.update(values)
        final_values = self._fill_values(model_values)
        return final_values

    def _page_render_validation(self, values, render_page, column_search):
        values = self.data_validation(values, column_search)
        if "error_msgs" in values.keys():
            return request.render(render_page, values)
        return True

    def data_validation(self, values, column_search):
        # model_id not defined
        values["model_id"] = values.get("model_id", False)
        values["model_name"] = values.get("model_name", False)
        if not values["model_id"]:
            return {
                "error_msgs": [
                    _(
                        f"model_id({values['model_id']}) param must be defined on the url in order to use the form"
                    )
                ],
                "global_error": True,
            }
        if not values["model_name"]:
            return {
                "error_msgs": [
                    _(
                        f"model_name({values['model_name']}) param must be defined on the url in order to use the form"
                    )
                ],
                "global_error": True,
            }

        # model_id not lost
        model = (
            request.env[values["model_name"]]
            .sudo()
            .search([("active", "=", False), (column_search, "=", values["model_id"])])
        )
        if model:
            return {
                "error_msgs": [_("Related model closed.")],
                "object_name": model.name,
                "display_success": False,
                "display_form": False,
                "closed_form": True,
            }
        # model_id not found
        model = (
            request.env[values["model_name"]]
            .sudo()
            .search([(column_search, "=", values["model_id"])])
        )
        if not model:
            return {
                "error_msgs": [
                    _(
                        f"Related model({values['model_name']}) not found. The url is not correct. model_id({values['model_id']}) param invalid."
                    )
                ],
                "global_error": True,
            }
        return values

    def get_values(self, values, column_search, data_main_fields):
        models = request.env[values["model_name"]].sudo().search(
            [(column_search, "=", values['model_id'])])
        model_values = {"closed": False}
        if models:
            model = models[0]
            for field_key in data_main_fields.keys():
                meta_line = model.metadata_line_ids.filtered(
                    lambda meta_data_line: meta_data_line.key == field_key
                )
                if meta_line:
                    model_values[field_key] = meta_line.value
        return model_values

#    def fill_values(self, values, display_success=False, display_form=True):

