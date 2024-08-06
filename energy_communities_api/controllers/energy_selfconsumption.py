from odoo.addons.base_rest.controllers import main


class EnergySelfconsumptionMainController(main.RestController):
    _root_path = "/api/energy-selfconsumption/"
    _collection_name = "energyselfconsumption.api.services"
    _default_auth = "jwt_energy_communities_auth"
