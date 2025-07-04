from odoo import _, api, fields, models

from .config import PACK_TYPE_NONE, PACK_TYPE_SELFCONSUMPTION


class ContractTemplate(models.Model):
    """
    Contract Template Extension for Self-consumption

    This model extends the base contract template functionality to support
    self-consumption pack types, including:
    - Pack type mixin integration
    - Custom pack type computation
    - Self-consumption specific template configuration
    """

    _name = "contract.template"
    _inherit = ["contract.template", "pack.type.mixin"]

    def custom_compute_pack_type(self):
        """
        Compute custom pack type for self-consumption templates

        Extends the base pack type computation to handle self-consumption
        specific pack types. If no pack type is detected, it checks for
        self-consumption pack configuration.
        """
        # Call parent method first
        super().custom_compute_pack_type()

        # If no pack type detected, check for self-consumption pack
        if self.pack_type == PACK_TYPE_NONE:
            self._set_custom_pack_type_on_contract_template(
                PACK_TYPE_SELFCONSUMPTION,
                "energy_selfconsumption.product_category_selfconsumption_pack",
            )

    def is_selfconsumption_template(self):
        """
        Check if this template is for self-consumption

        Returns:
            bool: True if self-consumption template, False otherwise
        """
        self.ensure_one()
        return self.pack_type == PACK_TYPE_SELFCONSUMPTION

    def get_selfconsumption_products(self):
        """
        Get products associated with self-consumption pack

        Returns:
            recordset: Products in the self-consumption category
        """
        self.ensure_one()

        if not self.is_selfconsumption_template():
            return self.env["product.product"]

        # Get self-consumption product category
        category = self.env.ref(
            "energy_selfconsumption.product_category_selfconsumption_pack",
            raise_if_not_found=False,
        )

        if not category:
            return self.env["product.product"]

        return self.env["product.product"].search(
            [("categ_id", "child_of", category.id)]
        )

    def validate_selfconsumption_template(self):
        """
        Validate template for self-consumption requirements

        Returns:
            bool: True if valid

        Raises:
            ValidationError: If validation fails
        """
        self.ensure_one()

        if not self.is_selfconsumption_template():
            return True

        errors = []

        # Check if template has required fields
        if not self.name:
            errors.append("Template name is required")

        # Check if template has contract lines
        if not self.contract_line_ids:
            errors.append("Self-consumption template must have contract lines")

        # Check if template has main line
        main_lines = self.contract_line_ids.filtered("main_line")
        if not main_lines:
            errors.append("Self-consumption template must have a main line")
        elif len(main_lines) > 1:
            errors.append("Self-consumption template can only have one main line")

        if errors:
            from odoo.exceptions import ValidationError

            raise ValidationError("\n".join(errors))

        return True
