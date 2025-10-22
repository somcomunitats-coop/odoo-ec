from odoo import fields, models

from odoo.addons.energy_communities_service_invoicing.config import (
    SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
)


class Product(models.Model):
    """
    Product Model Extension for Self-consumption

    This model extends the base product functionality to support
    self-consumption energy projects, including:
    - Contract template association
    - Self-consumption specific product configuration
    - Integration with contract generation workflows
    """

    _inherit = "product.product"

    # Contract template relationship
    contract_template_id = fields.Many2one(
        "contract.template",
        string="Contract Template",
        help="Contract template to use when creating contracts for this product",
    )

    # Business logic methods
    def has_contract_template(self):
        """
        Check if product has an associated contract template

        Returns:
            bool: True if has contract template, False otherwise
        """
        self.ensure_one()
        return bool(self.contract_template_id)

    def get_contract_template(self):
        """
        Get the contract template for this product

        Returns:
            contract.template: Contract template record or False
        """
        self.ensure_one()
        return self.contract_template_id

    def is_selfconsumption_product(self):
        """
        Check if this product is for self-consumption services

        Returns:
            bool: True if self-consumption product, False otherwise
        """
        self.ensure_one()

        # Check if product has self-consumption contract template
        if self.contract_template_id and hasattr(
            self.contract_template_id, "is_selfconsumption_template"
        ):
            return self.contract_template_id.is_selfconsumption_template()

        # Check if product is in self-consumption category
        selfconsumption_category = self.env.ref(
            SELFCONSUMPTION_PACK_PRODUCT_CATEG_REF,
            raise_if_not_found=False,
        )

        if selfconsumption_category and self.categ_id:
            return (
                self.categ_id.id == selfconsumption_category.id
                or selfconsumption_category.id
                in self.categ_id.parent_path.split("/")[:-1]
            )

        return False

    def create_contract_from_template(self, partner_id, **kwargs):
        """
        Create a contract from this product's template

        Args:
            partner_id (int): Partner ID for the contract
            **kwargs: Additional contract data

        Returns:
            contract.contract: Created contract record or False
        """
        self.ensure_one()

        if not self.has_contract_template():
            return False

        # Prepare contract data
        contract_data = {
            "partner_id": partner_id,
            "template_id": self.contract_template_id.id,
            "name": f"Contract for {self.name}",
        }
        contract_data.update(kwargs)

        # Create contract from template
        contract = self.env["contract.contract"].create(contract_data)

        return contract

    def get_product_summary(self):
        """
        Get summary information about the product

        Returns:
            dict: Product summary information
        """
        self.ensure_one()

        return {
            "name": self.name,
            "default_code": self.default_code,
            "has_contract_template": self.has_contract_template(),
            "template_name": self.contract_template_id.name
            if self.contract_template_id
            else None,
            "is_selfconsumption": self.is_selfconsumption_product(),
            "category": self.categ_id.name if self.categ_id else None,
            "list_price": self.list_price,
            "active": self.active,
        }
