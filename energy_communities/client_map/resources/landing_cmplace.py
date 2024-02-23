from odoo import _
from odoo.exceptions import UserError

from ...pywordpress_client.resources.authenticate import Authenticate
from ...pywordpress_client.resources.landing_page import (
    LandingPage as LandingPageResource,
)
from ..config import MapClientConfig


class LandingCmPlace:
    _name = "landing_cmplace"

    def __init__(self, landing):
        self.landing = landing
        self.wp_landing_data = self._get_wp_landing_data()
        button_configs = self._get_button_color_configs()
        if button_configs["errors"]:
            raise UserError(error_msg)
        else:
            self.button_configs = button_configs["button_color_configs"]

    def create(self):
        """
        Creates a place from a landing instance.
        """
        self._create_update_place("create")

    def update(self):
        """
        Updates a place from a landing instance.
        """
        self._create_update_place("update")

    def _create_update_place(self, mode):
        validated_place_data = self._validate_and_prepare_place_data()
        if validated_place_data["errors"]:
            error_msg = ""
            for error in validated_place_data["errors"]:
                error_msg += error + "\n"
            raise UserError(error_msg)
        else:
            if mode == "create":
                place = self.landing.env["cm.place"].create(
                    validated_place_data["data"]
                )
                self.landing.write({"map_place_id": place.id})
            if mode == "update":
                place = self.landing.map_place_id
                if place:
                    place.write(validated_place_data["data"])
            if place:
                self._place_extra_data_setup(place)

    def _place_extra_data_setup(self, place):
        place.setup_slug_id()
        place.build_presenter_metadata_ids()
        # setup description
        self._setup_place_description(place)
        # setup external links
        self._setup_external_links(place)
        # apply translations
        self._apply_place_metadatas_translations(place)

    def _validate_and_prepare_place_data(self):
        """
        Try to generate a place data dictionary and collect errors if they're
        @returns: dictionary with 'data' key as the dict to be used for place creation or update and 'errors' key to collect errors if they're
        """
        ret_dict = {
            "data": {
                "company_id": MapClientConfig.MAPPING__INSTANCE_ID,
                "name": self.landing.name,
                "type": "place",
                "status": MapClientConfig.MAPPING__LANDING_STATUS__MAP_PLACE_STATUS[
                    self.landing.status
                ],
                "interaction_method": "external_link",
                "filter_mids": [(5, 0, 0)],
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
        map = self.landing.env["cm.map"].search(
            [("slug_id", "=", MapClientConfig.MAPPING__MAP)]
        )
        if map:
            ret_dict["data"]["map_id"] = map.id
        else:
            ret_dict["errors"].append(
                _("Map not found slug_id: {}").format(self.MAPPING__MAP)
            )
        # Lat and Lng
        if self.landing.lat:
            ret_dict["data"]["lat"] = self.landing.lat
        else:
            ret_dict["errors"].append(
                _("Landing lat param required for place creation")
            )
        if self.landing.lng:
            ret_dict["data"]["lng"] = self.landing.lng
        else:
            ret_dict["errors"].append(
                _("Landing lng param required for place creation")
            )
        # Place category
        categories = self.landing.env["cm.place.category"].search([])
        place_category_slug = (
            MapClientConfig.MAPPING__LANDING_COMMUNITY_TYPE__MAP_CATEGORY[
                self.landing.community_type
            ]
        )
        place_category = categories.filtered(lambda r: r.slug_id == place_category_slug)
        if place_category:
            ret_dict["data"]["place_category_id"] = place_category.id
        else:
            ret_dict["errors"].append(
                _("Place category not found slug_id: {}").format(place_category_slug)
            )
        # Community status filter
        filters = self.landing.env["cm.filter"].search([])
        place_community_status_slug = (
            MapClientConfig.MAPPING__LANDING_COMMUNITY_STATUS__MAP_FILTER[
                self.landing.community_status
            ]
        )
        place_community_status = filters.filtered(
            lambda r: r.slug_id == place_community_status_slug
        )
        if place_community_status:
            ret_dict["data"]["marker_color"] = place_community_status.id
            ret_dict["data"]["filter_mids"].append((4, place_community_status.id))
        else:
            ret_dict["errors"].append(
                _("Place status filter not found slug_id: {}").format(
                    place_community_status_slug
                )
            )
        # Community active services
        for service in self.landing.community_active_services:
            service_slug = MapClientConfig.MAPPING__LANDING_ACTIVE_SERVICES__MAP_FILTER[
                service.tag_ext_id
            ]
            place_service = filters.filtered(lambda r: r.slug_id == service_slug)
            if place_service:
                ret_dict["data"]["filter_mids"].append((4, place_service.id))
            else:
                ret_dict["errors"].append(
                    _("Place status filter not found slug_id: {}").format(service_slug)
                )
        # Presenter
        presenter_name = (
            MapClientConfig.MAPPING__LANDING_COMMUNITY_STATUS__MAP_PRESENTER[
                self.landing.community_status
            ]
        )
        presenter = self.landing.env["cm.presenter.model"].search(
            [("name", "=", presenter_name)]
        )
        if presenter:
            ret_dict["data"]["presenter_model_id"] = presenter.id
        else:
            ret_dict["errors"].append(
                _("Place presenter not found slug_id: {}").format(presenter_name)
            )
        return ret_dict

    def _get_address_txt(self):
        address_txt = ""
        if self.landing.street:
            address_txt = self.landing.street
        if self.landing.postal_code:
            if address_txt == "":
                address_txt = self.landing.postal_code
            else:
                address_txt += ", " + self.landing.postal_code
        if self.landing.city:
            if address_txt == "":
                address_txt = self.landing.city
            else:
                address_txt += ", " + self.landing.city
        return address_txt

    def _get_button_color_configs(self):
        ret_dict = {"button_color_configs": {}, "errors": []}
        button_color_configs = self.landing.env["cm.button.color.config"].search([])
        ret_dict["button_color_configs"]["green"] = button_color_configs.filtered(
            lambda r: r.name
            == MapClientConfig.MAPPING__BUTTON_COLOR_CONFIG_NAME["green"]
        )
        ret_dict["button_color_configs"]["yellow"] = button_color_configs.filtered(
            lambda r: r.name
            == MapClientConfig.MAPPING__BUTTON_COLOR_CONFIG_NAME["yellow"]
        )
        if (
            not ret_dict["button_color_configs"]["green"]
            or not ret_dict["button_color_configs"]["yellow"]
        ):
            ret_dict["errors"] = _("Button configs not found.")
        return ret_dict

    def _get_wp_landing_data(self):
        instance_company = self.landing.env["res.company"].search(
            [("hierarchy_level", "=", "instance")]
        )
        if instance_company:
            baseurl = instance_company.wordpress_base_url
            username = instance_company.wordpress_db_username
            password = instance_company.wordpress_db_password
            auth = Authenticate(baseurl, username, password).authenticate()
            token = "Bearer %s" % auth["token"]
            landing_page_wp_data = LandingPageResource(
                token, baseurl, self.landing.wp_landing_page_id
            ).get()
            return landing_page_wp_data
        return False

    def _setup_place_description(self, place):
        desc_meta = self.landing.env["cm.place.presenter.metadata"].search(
            [
                ("place_id", "=", place.id),
                ("key", "=", MapClientConfig.MAPPING__OPEN_PLACE_DESCRIPTION_META_KEY),
            ]
        )
        desc_meta.write({"value": self.landing.short_description})

    def _setup_external_links(self, place):
        new_external_links_ids = []
        existing_external_links = self.landing.env["cm.place.external.link"].search(
            [("place_id", "=", place.id)]
        )
        if self.landing.allow_new_members:
            new_external_links_ids.append(
                self._become_cooperator_external_link(place.id).id
            )
        else:
            new_external_links_ids.append(self._contact_external_link(place).id)
        new_external_links_ids.append(self._landing_external_link(place).id)
        # remove old external_links if needed
        for existing_external_link in existing_external_links:
            if existing_external_link.id not in new_external_links_ids:
                existing_external_link.unlink()

    def _get_or_create_external_link(
        self, place_id, name, url, target, button_color_config_id, sort_order
    ):
        existing_external_links = self.landing.env["cm.place.external.link"].search(
            [
                ("place_id", "=", place_id),
                ("name", "=", name),
                ("url", "=", url),
                ("target", "=", target),
                ("button_color_config_id", "=", button_color_config_id),
                ("sort_order", "=", sort_order),
            ]
        )
        if existing_external_links:
            return existing_external_links[0]
        else:
            return self.landing.env["cm.place.external.link"].create(
                {
                    "place_id": place_id,
                    "name": name,
                    "url": url,
                    "target": target,
                    "button_color_config_id": button_color_config_id,
                    "sort_order": sort_order,
                }
            )

    def _become_cooperator_external_link(self, place_id):
        external_link = self._get_or_create_external_link(
            place_id,
            MapClientConfig.MAPPING__EXTERNAL_LINK__BECOME_COOPERATOR__LINK_LABEL[
                "ca_ES"
            ],
            "{base_url}/become_cooperator?odoo_company_id={odoo_company_id}".format(
                base_url=self.landing.env["ir.config_parameter"].get_param(
                    "web.base.url"
                ),
                odoo_company_id=self.landing.company_id.id,
            ),
            "_blank",
            self.button_configs["yellow"].id,
            0,
        )
        # es_ES Translation
        self._update_translation(
            "cm.place.external.link,name",
            external_link.id,
            MapClientConfig.MAPPING__EXTERNAL_LINK__BECOME_COOPERATOR__LINK_LABEL[
                "ca_ES"
            ],
            MapClientConfig.MAPPING__EXTERNAL_LINK__BECOME_COOPERATOR__LINK_LABEL[
                "es_ES"
            ],
            "es_ES",
        )
        self._update_translation(
            "cm.place.external.link,url",
            external_link.id,
            "{base_url}/become_cooperator?odoo_company_id={odoo_company_id}".format(
                base_url=self.landing.env["ir.config_parameter"].get_param(
                    "web.base.url"
                ),
                odoo_company_id=self.landing.company_id.id,
            ),
            "{base_url}/es/become_cooperator?odoo_company_id={odoo_company_id}".format(
                base_url=self.landing.env["ir.config_parameter"].get_param(
                    "web.base.url"
                ),
                odoo_company_id=self.landing.company_id.id,
            ),
            "es_ES",
        )
        return external_link

    def _contact_external_link(self, place):
        external_link = self._get_or_create_external_link(
            place.id,
            MapClientConfig.MAPPING__EXTERNAL_LINK__CONTACT__LINK_LABEL["ca_ES"],
            "{landing_link}/#contacte".format(
                landing_link=self.wp_landing_data["link"]
            ),
            "_top",
            self.button_configs["yellow"].id,
            0,
        )
        # es_ES Translation
        self._update_translation(
            "cm.place.external.link,name",
            external_link.id,
            MapClientConfig.MAPPING__EXTERNAL_LINK__CONTACT__LINK_LABEL["ca_ES"],
            MapClientConfig.MAPPING__EXTERNAL_LINK__CONTACT__LINK_LABEL["es_ES"],
            "es_ES",
        )
        if self.wp_landing_data["translations"]:
            if "es" in self.wp_landing_data["translations"].keys():
                self._update_translation(
                    "cm.place.external.link,url",
                    external_link.id,
                    "{landing_link}/#contacte".format(
                        landing_link=self.wp_landing_data["link"]
                    ),
                    "{landing_link}/#contacte".format(
                        landing_link=self.wp_landing_data["translations"]["es"]
                    ),
                    "es_ES",
                )
        return external_link

    def _landing_external_link(self, place):
        external_link = self._get_or_create_external_link(
            place.id,
            MapClientConfig.MAPPING__EXTERNAL_LINK__LANDING__LINK_LABEL["ca_ES"],
            self.wp_landing_data["link"],
            "_top",
            self.button_configs["green"].id,
            1,
        )
        # setup social sahreable url for better sharing
        place.write({"social_shareable_url": self.wp_landing_data["link"]})
        # es_ES Translation
        self._update_translation(
            "cm.place.external.link,name",
            external_link.id,
            MapClientConfig.MAPPING__EXTERNAL_LINK__LANDING__LINK_LABEL["ca_ES"],
            MapClientConfig.MAPPING__EXTERNAL_LINK__LANDING__LINK_LABEL["es_ES"],
            "es_ES",
        )
        if self.wp_landing_data["translations"]:
            if "es" in self.wp_landing_data["translations"].keys():
                self._update_translation(
                    "cm.place.external.link,url",
                    external_link.id,
                    self.wp_landing_data["link"],
                    self.wp_landing_data["translations"]["es"],
                    "es_ES",
                )
                self._update_translation(
                    "cm.place,social_shareable_url",
                    place.id,
                    self.wp_landing_data["link"],
                    self.wp_landing_data["translations"]["es"],
                    "es_ES",
                )
        return external_link

    def _apply_place_metadatas_translations(self, place):
        for lang_code in self._get_active_languages():
            # place description: applied from landing short_description already translated
            landing_short_description_trans = self._get_translation(
                "landing.page,short_description",
                self.landing.id,
                lang_code,
                translated=True,
            )
            if landing_short_description_trans:
                self._apply_place_metadata_translation(
                    place.id,
                    MapClientConfig.MAPPING__OPEN_PLACE_DESCRIPTION_META_KEY,
                    landing_short_description_trans.src,
                    landing_short_description_trans.value,
                    lang_code,
                )
        # place social headline: es_ES
        self._apply_place_metadata_translation(
            place.id,
            MapClientConfig.MAPPING__OPEN_PLACE_SOCIAL_HEADLINE_META_KEY,
            MapClientConfig.MAPPING__OPEN_PLACE_SOCIAL_HEADLINE_ORIGINAL,
            MapClientConfig.MAPPING__OPEN_PLACE_SOCIAL_HEADLINE_TRANSLATION["es_ES"],
            "es_ES",
        )

    def _apply_place_metadata_translation(
        self, place_id, meta_key, original_value, trans_value, lang
    ):
        related_meta = self.landing.env["cm.place.presenter.metadata"].search(
            [("place_id", "=", place_id), ("key", "=", meta_key)]
        )
        if related_meta:
            self._update_translation(
                "cm.place.presenter.metadata,value",
                related_meta.id,
                original_value,
                trans_value,
                lang,
            )

    # TODO: Make all this translation block more compliant with ir.translation model
    def _get_active_languages(self):
        return self.landing.env["res.lang"].search([("active", "=", 1)]).mapped("code")

    def _get_translation(self, translation_name, res_id, lang, translated=False):
        query = [
            ("name", "=", translation_name),
            ("res_id", "=", res_id),
            ("lang", "=", lang),
        ]
        if translated:
            query.append(("state", "=", "translated"))
        return self.landing.env["ir.translation"].search(query)

    def _update_translation(
        self, translation_name, res_id, original_value, trans_value, lang
    ):
        translation = self._get_translation(translation_name, res_id, lang)
        if translation:
            translation.write(
                {"src": original_value, "value": trans_value, "state": "translated"}
            )
        else:
            self.landing.env["ir.translation"].create(
                {
                    "name": translation_name,
                    "res_id": res_id,
                    "lang": lang,
                    "type": "model",
                    "src": original_value,
                    "value": trans_value,
                    "state": "translated",
                }
            )
