from odoo.addons.base_rest.controllers import main


class MainController(main.RestController):
    _root_path = "/api/"
    _collection_name = "ce.services"
    _default_auth = "api_key"
