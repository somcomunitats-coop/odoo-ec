from odoo.addons.base.models.res_users import Users
from odoo.addons.component.core import Component


class UserCreator(Component):
    _name = "user.creator"
    _usage = "user.create"
    _apply_on = "res.users"
    _collection = "utils.backend"

    def create_user(self) -> Users:
        print("HERE!!!!")
        __import__("ipdb").set_trace()
        return True
