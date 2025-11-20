from odoo import http
from odoo.http import request
from odoo.tools.translate import _


class WebsiteShareSubscriptionController(http.Controller):
    @http.route(
        [
            "/subscription/<string:mode>/<string:company_ext_id>",
            "/subscription/<string:mode>/<string:company_ext_id>/<string:product_ext_id>",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def subsctiption_page(self, **kwargs):
        if "product_ext_id" not in kwargs.keys():
            product_ext_id = False
        company = self._get_model_from_ext_id("res.company", company_ext_id)
        product = self._get_model_from_ext_id("product.template", product_ext_id)
        self._validate_request(mode, company, product)
        __import__("ipdb").set_trace()
        if mode == "member":
            self._member_page()

    def _validate_request(mode, company, product):
        pass

    def _get_model_from_ext_id(model_name, ext_id):
        pass

    def _member_page(self):
        return request.render("cooperator_website.becomecooperator", values)
