from odoo import http
from odoo.http import request
from odoo.tools.translate import _


# http://odoo-ce.local:8069/es/subscription/member/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_invited/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_voluntary/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/company_menber/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
# http://odoo-ce.local:8069/es/subscription/error/356a192b7913b04c54574d18c28d46e6395428ab/ae7329c979b3cd96086c22cca6217764ab3e50ec
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
        # Default kwargs
        mode = False
        company_ext_id = False
        product_ext_id = False
        if "mode" in kwargs.keys():
            mode = kwargs.get("mode", False)
        if "company_ext_id" in kwargs.keys():
            company_ext_id = kwargs.get("company_ext_id", False)
        if "product_ext_id" in kwargs.keys():
            product_ext_id = kwargs.get("product_ext_id", False)
        # Get the company and product from the external ID
        company = self._get_model_from_ext_id(
            "res.company", "company_external_id", company_ext_id
        )
        # Get the product from the external ID
        product = self._get_model_from_ext_id(
            "product.template", "product_external_id", product_ext_id
        )
        # Validate the request
        values = self._validate_request(mode, company, product)
        # Render the page
        return self.render(values)

    def _get_model_from_ext_id(self, model_name, field_name, ext_id):
        if ext_id:
            return request.env[model_name].sudo().search([(field_name, "=", ext_id)])
        return False

    def _validate_request(self, mode, company, product):
        values = {}
        if mode not in ["member", "invited", "company", "company_invited"]:
            values.update({"model": "error", "error_msgs": ["Invalid mode"]})
            return values
        if not company:
            values.update({"model": "error", "error_msgs": ["Company not found"]})
            return values
        if not product:
            values.update({"model": "error", "error_msgs": ["Product not found"]})
            return values
        return self._fill_values(mode, values, company, product)

    def _fill_values(self, mode, values, company, product):
        values.update(
            {
                # General values
                # Company values
                "company_id": company.id,
                "company_name": company.name,
                "company.address": company.address,
                "company_city": company.city,
                "company_state": company.state,
                "company_zip": company.zip,
                "company_country": company.country,
                "company_email": company.email,
                "company_phone": company.phone,
                "company_website": company.website,
                # Product values
                "product_id": product.id,
                "product_name": product.name,
                "product_description": product.description,
                "product_price": product.list_price,
                # Mode values
                "model": mode,
            }
        )
        return values

    def _render_page(self, template_name, values):
        return request.render(template_name, values)

    def render(self, values):
        return self._render_page(
            "energy_communities_cooperator.subcription_data_page", values
        )
