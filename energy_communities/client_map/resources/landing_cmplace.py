from odoo import _
from odoo.exceptions import UserError


class LandingCmPlace:
    _name = "landing_cmplace"

    # mapping between landings params and place params
    _MAPPING__INSTANCE_ID = 1
    _MAPPING__LANDING_ACTIVE_SERVICES__MAP_FILTER = {
        "ce_tag_common_generation": "generacio-renovable-comunitaria",
        "ce_tag_energy_efficiency": "eficiencia-energetica",
        "ce_tag_sustainable_mobility": "mobilitat-sostenible",
        "ce_tag_citizen_education": "formacio-ciutadana",
        "ce_tag_thermal_energy": "energia-termica-i-climatitzacio",
        "ce_tag_collective_purchases": "compres-col-lectives",
        "ce_tag_renewable_energy": "subministrament-d-energia-100-renovable",
        "ce_tag_aggregate_demand": "agregacio-i-flexibilitat-de-la-demanda",
    }
    _MAPPING__MAP = "campanya"
    _MAPPING__LANDING_COMMUNITY_STATUS__MAP_FILTER = {"open": "oberta"}
    _MAPPING__LANDING_STATUS__MAP_PLACE_STATUS = {
        "draft": "draft",
        "publish": "published",
    }
    _MAPPING__LANDING_COMMUNITY_TYPE__MAP_CATEGORY = {
        "citizen": "ciutadania",
        "industrial": "industrial",
    }
    _MAPPING__LANDING_COMMUNITY_STATUS__MAP_PRESENTER = {"open": "CE Oberta"}

    def __init__(self, landing):
        self.landing = landing

    def create(self):
        """
        Creates a place from a landing instance.
        """
        validate_creation_dict = self._validate_and_prepare_creation()
        print(validate_creation_dict)
        if validate_creation_dict["errors"]:
            error_msg = ""
            for error in validate_creation_dict["errors"]:
                error_msg += error + "\n"
            raise UserError(error_msg)
        else:
            place = self.landing.env["cm.place"].create(
                validate_creation_dict["creation_data"]
            )
            place._get_slug_id()
            place.build_presenter_metadata_ids()
            # setup description
            desc_meta = self.landing.env["cm.place.presenter.metadata"].search(
                [("place_id", "=", place.id), ("key", "=", "po2_description")]
            )
            desc_meta.write({"value": self.landing.short_description})
            # relate place with landing
            self.landing.write({"map_place_id": place.id})
        return True

    # def update(self):
    #     """
    #     Updates a place from a landing instance.
    #     """
    #     response_data = Client(self.baseurl).put(
    #         "{url_path}/{id}".format(url_path=self._url_path, id=self.id),
    #         self.token,
    #         body,
    #     )
    #     return response_data

    def _validate_and_prepare_creation(self):
        """
        Try to generate a place creation dictionary and collect errors if they're
        @returns: dictionary with 'creatrion_data' key as the dict to be used for place creation and 'errors' key to collect errors if they're
        """
        ret_dict = {
            "creation_data": {
                "company_id": self._MAPPING__INSTANCE_ID,
                "name": self.landing.name,
                "type": "place",
                "status": self._MAPPING__LANDING_STATUS__MAP_PLACE_STATUS[
                    self.landing.status
                ],
                "interaction_method": "external_link",
                "external_link_ids": [],
                "filter_mids": [],
                "address_txt": self._get_address_txt(),
            },
            "errors": [],
        }
        # Permissions
        # TODO: Decide the permission level for this action
        if self.landing.env.user.company_id.hierarchy_level not in [
            "coordinator",
            "instance",
        ]:
            ret_dict["errors"].append(
                _(
                    "Only users that belongs to the 'Coordinator' or 'Instance' company can create new Map Places."
                )
            )
        # Map reference
        map = self.landing.env["cm.map"].search([("slug_id", "=", self._MAPPING__MAP)])
        if map:
            ret_dict["creation_data"]["map_id"] = map.id
        else:
            ret_dict["errors"].append(
                _("Map not found slug_id: {}").format(self._MAPPING__MAP)
            )
        # Lat and Lng
        if self.landing.lat:
            ret_dict["creation_data"]["lat"] = self.landing.lat
        else:
            ret_dict["errors"].append(
                _("Landing lat param required for place creation")
            )
        if self.landing.lng:
            ret_dict["creation_data"]["lng"] = self.landing.lng
        else:
            ret_dict["errors"].append(
                _("Landing lng param required for place creation")
            )
        # Place category
        categories = self.landing.env["cm.place.category"].search([])
        place_category_slug = self._MAPPING__LANDING_COMMUNITY_TYPE__MAP_CATEGORY[
            self.landing.community_type
        ]
        place_category = categories.filtered(lambda r: r.slug_id == place_category_slug)
        if place_category:
            ret_dict["creation_data"]["place_category_id"] = place_category.id
        else:
            ret_dict["errors"].append(
                _("Place category not found slug_id: {}").format(place_category_slug)
            )
        # Community status filter
        filters = self.landing.env["cm.filter"].search([])
        place_community_status_slug = (
            self._MAPPING__LANDING_COMMUNITY_STATUS__MAP_FILTER[
                self.landing.community_status
            ]
        )
        place_community_status = filters.filtered(
            lambda r: r.slug_id == place_community_status_slug
        )
        if place_community_status:
            ret_dict["creation_data"]["marker_color"] = place_community_status.id
            ret_dict["creation_data"]["filter_mids"].append(
                (4, place_community_status.id)
            )
        else:
            ret_dict["errors"].append(
                _("Place status filter not found slug_id: {}").format(
                    place_community_status_slug
                )
            )
        # Community active services
        # FINISH THIS!!!!
        for service in self.landing.community_active_services:
            service_slug = self._MAPPING__LANDING_ACTIVE_SERVICES__MAP_FILTER[
                service.tag_ext_id
            ]
        # Presenter
        presenter_name = self._MAPPING__LANDING_COMMUNITY_STATUS__MAP_PRESENTER[
            self.landing.community_status
        ]
        presenter = self.landing.env["cm.presenter.model"].search(
            [("name", "=", presenter_name)]
        )
        if presenter:
            ret_dict["creation_data"]["presenter_model_id"] = presenter.id
        else:
            ret_dict["errors"].append(
                _("Place status filter not found slug_id: {}").format(presenter_name)
            )
        return ret_dict

    def _get_address_txt(self):
        address_txt = ""
        if self.landing.street:
            address_txt += self.landing.street
        if self.landing.postal_code:
            if address_txt == "":
                address_txt += self.landing.postal_code
            else:
                address_txt += ", " + self.landing.postal_code
        if self.landing.city:
            if address_txt == "":
                address_txt += self.landing.city
            else:
                address_txt += " " + self.landing.city
        return address_txt
