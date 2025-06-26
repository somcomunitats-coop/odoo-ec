from odoo.addons.component.core import Component


class ProductUtils(Component):
    _inherit = "product.utils"

    def create_product(self):
        __import__("ipdb").set_trace()
        print("HERE")
