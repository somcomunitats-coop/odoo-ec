from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from ..config import MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF


# http://odoo-ce.local:8069/es/subscription/member/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_member/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
class WebsiteShareSubscriptionController(http.Controller):
    mode = None
    company = None
    product_categ = None
    product = None
    values = {}

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
        """
        This function is used to render the subscription page. It is called when the user visits the subscription page.
        It validates the request and renders the page.
        Args:
            mode: The mode of the subscription page.
            company_ext_id: The external ID of the company.
            product_ext_id: The external ID of the product.
        Returns:
            The rendered page.
        """
        self._setup_class_defaults(kwargs)
        self._get_base_values()
        # Validate the request
        self._validate_request()
        if not "global_error" in self.values.keys():
            self._get_extended_values()
        # Render the page
        return self.render_page()

    def _setup_class_defaults(self, kwargs):
        self.mode = kwargs.get("mode")
        # Get the company and product from the external ID
        self.company = self._get_model_from_ext_id(
            "res.company", "company_external_id", kwargs.get("product_ext_id")
        )
        product_ext_id = False
        if "product_ext_id" in kwargs.keys():
            product_ext_id = kwargs.get("product_ext_id")
        # Get the product from the external ID
        self.product = self._get_model_from_ext_id(
            "product.template", "product_external_id", product_ext_id
        )
        self.product_categ = request.env.ref(
            MAPPING__SUBSCRIPTION_MODE__PRODUCT_CATEG_REF[self.mode]
        )

    def _get_base_values(self):
        __import__("ipdb").set_trace()
        self.values |= {
            # template_mode =
            # "page_title": self._get_page_title()
        }

    def _validate_request(self):
        # if mode not in ["member", "invited", "company", "company_invited"]:
        #     values.update({"global_error": True, "error_msgs": ["Invalid mode"]})
        #     return values
        # if not company:
        #     values.update({"global_error": True, "error_msgs": ["Company not found"]})
        #     return values
        # if not product:
        #     values.update({"global_error": True, "error_msgs": ["Product not found"]})
        #     return values
        pass

    def _get_extended_values(self):
        # values.update(
        #     {
        #     }
        # )
        pass

    def _render_page(self, values):
        return request.render(
            "energy_communities_cooperator.website_template_subscription_base",
            self.values,
        )

    # getters
    def _get_model_from_ext_id(self, model_name, field_name, ext_id):
        if ext_id:
            return request.env[model_name].sudo().search([(field_name, "=", ext_id)])
        return False
