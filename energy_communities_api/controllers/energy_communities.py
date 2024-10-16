from odoo.addons.base_rest.controllers import main


class MemberProfileController(main.RestController):
    _root_path = "/api/energy-communities/"
    _collection_name = "energy_communities_member.api.services"
    _default_auth = "jwt_energy_communities_auth"


class EnergyCommunitiesController(main.RestController):
    _root_path = "/api/communities/"
    _collection_name = "energy_communities.api.services"
    _default_auth = "jwt_energy_communities_auth"
