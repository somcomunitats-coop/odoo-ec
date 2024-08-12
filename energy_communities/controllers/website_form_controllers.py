from odoo import _, http
from odoo.http import request

class WebsiteFormController(http.Controller):

    # Controlador principal para obtener los datos de renderizado del formulario
    # y visualizar el formulario
    def display_data_page(self, values, render_page, column_search):
        response = self._page_render_validation(values, render_page, column_search)
        if response is not True:
            return response
        # prefill values
        model_values = self._get_values(values, column_search)
        model_values.update(values)
        final_values = self._fill_values(model_values)
        return final_values

    def data_submit(self, column_search, **kwargs):
        # model_id validation
        response = self._page_render_validation(kwargs,
                                                self.get_data_page_url(kwargs),
                                                "id")
        if response is not True:
            return response

        model = (
            request.env[kwargs["model_name"]]
            .sudo()
            .search([(column_search, "=", kwargs["model_id"])])
        )

        # data structures contruction
        values, form_values = self.get_data_custom_submit()

        # avoid form resubmission by accessing /submit url
        if form_values:
            # validation
            response = self._form_submit_validation(values)
            if response is not True:
                return response
            # metadata processing
            self._process_lead_metadata(model, values)
            # success
            return self.get_form_submit_url(values)
        else:
            return request.redirect(self.get_data_page_url(values))

    def get_data_custom_submit(self):
        values = {}
        form_values = {}
        return values, form_values

    def _page_render_validation(self, values, render_page, column_search):
        values = self._data_validation(values, column_search)
        if "error_msgs" in values.keys():
            return request.render(render_page, values)
        return True

    def _data_validation(self, values, column_search):
        # model_id not defined
        values["model_id"] = values.get("model_id", False)
        values["model_name"] = values.get("model_name", self.get_model_name())
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
        values = self.data_validation_custom(values)
        return values

    def get_model_name(self):
        return False
    # Inherit the custom data validation
    def data_validation_custom(self, values):
        return values

    def _get_values(self, values, column_search):
        models = request.env[values["model_name"]].sudo().search(
            [(column_search, "=", values['model_id'])])
        model_values = {"closed": False}
        if models:
            model = models[0]
            data_main_fields = self.get_data_main_fields()
            model_values = self.get_extra_data_main_fields(model, model_values)
        return model_values

    # Inherit the custom data fields
    def get_extra_data_main_fields(self, model, model_values):
        return model_values

    # Inherit the custom data fields
    def get_data_main_fields(self):
        return {}

    def _fill_values(self, values, display_success=False, display_form=True, data_fields={}):
        # urls
        values["page_url"] = self.get_community_data_page_url(values)
        values["form_submit_url"] = self.get_community_form_submit_url(values)
        # form labels
        # form keys
        for field_key in data_fields.keys():
            values[field_key + "_label"] = self.get_translate_field_label(data_fields,
                                                                          values,
                                                                          field_key)
            values[field_key + "_key"] = field_key
        # language selection
        values["lang_options"] = self._get_langs()
        if "current_lang" not in values.keys() or values["current_lang"] == "":
            values["current_lang"] = False
        values = self.get_fill_values_custom(values)
        # form/messages visibility
        values["display_success"] = display_success
        values["display_form"] = display_form
        values["closed_form"] = False
        if "closed" in values.keys():
            values["closed_form"] = values["closed"]
        return values

    def get_data_page_url(self, values):
        return ""

    def get_form_submit_url(self, values):
        return ""

    def get_translate_field_label(self, data_fields, values, field_key):
        return ""

    def get_fill_values_custom(self, values):
        return values




