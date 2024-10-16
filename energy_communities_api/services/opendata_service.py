from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component, WorkContext

from ..schemas import NetworkInfo, NetworkInfoResponse
from ..utils import api_info, single_response


class OpenDataNetworkService(Component):
    _inherit = ["base.rest.service"]
    _name = "opendata_network.api.service"
    _collection = "opendata.api.services"
    _usage = "network"
    _description = """
        Set of endpoints that return opendata about energy communites
    """

    @restapi.method(
        [(["/"], "GET")],
        output_param=PydanticModel(NetworkInfoResponse),
    )
    def network(self):
        """
        Basic opendata information about energy communities
        """
        backend = self.env["api.info.backend"].browse(1)
        with backend.work_on("api.info.backend", schema_class=NetworkInfo) as work:
            component = work.component(usage="opendata.info")
            network_info = component.get_network_metrics()
        return single_response(request, NetworkInfoResponse, network_info)
