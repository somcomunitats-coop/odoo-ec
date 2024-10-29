from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import Component

from ..schemas import EnergyCommunityInfo, EnergyCommunityInfoResponse
from ..utils import api_info, single_response


class EnergyCommunityApiService(Component):
    _inherit = ["base.rest.service", "api.service.utils"]
    _name = "energy_community.api.service"
    _collection = "energy_communities.api.services"
    _usage = "communities"
    _description = """
        Set of enpoints that retrieve and manage information about energy communities
    """
    _work_on_model = "res.company"

    def __init__(self, *args):
        super().__init__(*args)

    @restapi.method(
        [(["/<int:community_id>"], "GET")],
        output_param=PydanticModel(EnergyCommunityInfoResponse),
    )
    def energy_community(self, community_id):
        """
        Basic personal information
        """
        self._validate_headers()
        member_community_id = request.httprequest.headers.get("CommunityId")
        with api_info(
            self.env,
            self._work_on_model,
            EnergyCommunityInfo,
            member_community_id,
        ) as component:
            community_info = component.get_energy_community_info(community_id)
        return single_response(request, EnergyCommunityInfoResponse, community_info)
