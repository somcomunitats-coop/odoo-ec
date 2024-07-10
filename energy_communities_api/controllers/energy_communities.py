from odoo.addons.base_rest.controllers import main


class MemberProfileController(main.RestController):
    _root_path = "/api/"
    _collection_name = "energy_communities_member.api.services"
    _default_auth = "api_key"
    # _default_auth = "kc_jwt_auth"
