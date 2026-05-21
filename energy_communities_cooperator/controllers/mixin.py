from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.translate import _


class Controller_company_and_product_mixin:
    def get_company_and_product(self, **kwargs):
        target_odoo_company_id = False
        if kwargs.get("odoo_company_id", False):
            try:
                target_odoo_company_id = (
                    request.env["res.company"]
                    .sudo()
                    .search(
                        [
                            (
                                "id",
                                "=",
                                kwargs.get("odoo_company_id"),
                            )
                        ]
                    )
                )
            except:
                pass

        if not target_odoo_company_id and kwargs.get("external_company_id", False):
            try:
                target_odoo_company_id = (
                    request.env["res.company"]
                    .sudo()
                    .search(
                        [
                            (
                                "company_external_id",
                                "=",
                                kwargs.get("external_company_id"),
                            )
                        ]
                    )
                )
            except:
                pass

        if not target_odoo_company_id:
            raise ValidationError(
                _(
                    "Not valid parameter value [odoo_company_id] or [external_company_id]"
                )
            )

        target_product_external_id = False
        if kwargs.get("product_external_id", False):
            try:
                target_product_external_id = (
                    request.env["product.template"]
                    .sudo()
                    .search(
                        [
                            (
                                "product_external_id",
                                "=",
                                kwargs.get("product_external_id"),
                            )
                        ]
                    )
                    .id
                )
            except:
                pass

        if ("product_external_id" in kwargs) and (not target_product_external_id):
            try:
                target_product_external_id = (
                    request.env["product.template"]
                    .sudo()
                    .search(
                        [
                            (
                                "id",
                                "=",
                                kwargs.get("product_external_id"),
                            )
                        ]
                    )
                )
            except:
                pass

            if not target_product_external_id:
                raise ValidationError(
                    _("Not valid parameter value [product_external_id]")
                )
        return target_odoo_company_id, target_product_external_id
