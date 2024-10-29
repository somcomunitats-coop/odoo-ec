from odoo.addons.base_rest.controllers import main


class OpenDataController(main.RestController):
    _root_path = "/api/opendata/"
    _collection_name = "opendata.api.services"
    _default_auth = "public"
