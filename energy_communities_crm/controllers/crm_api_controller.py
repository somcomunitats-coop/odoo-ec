from odoo.addons.base_rest.controllers import main


class CrmApiController(main.RestController):
    _root_path = "/api/crm/"
    _collection_name = "crm.api.services"
    _default_auth = "api_key"
