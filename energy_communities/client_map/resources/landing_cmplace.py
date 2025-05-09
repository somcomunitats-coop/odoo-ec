from odoo import _
from odoo.exceptions import UserError

from ...pywordpress_client.resources.authenticate import Authenticate
from ...pywordpress_client.resources.landing_page import (
    LandingPage as LandingPageResource,
)
from ..config import LandingClientConfig, MapClientConfig


class LandingCmPlace:
    _name = "landing_cmplace"

    def __init__(self, landing):
        self.landing = landing
        self.wp_landing_data = self._get_wp_landing_data()
        button_configs = self._get_button_color_configs()
        if button_configs["errors"]:
            raise UserError(button_configs["errors"])
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

    def restore_cooperator_button_defaults(self, cooperator_button):
        self._apply_cooperator_button_translations(cooperator_button)
        self._create_update_place("update")

    def _create_update_place(self, mode):
        self._setup_landing_cooperator_buttons()
        if mode == "create":
            for map_slug in MapClientConfig.MAPPING__MAPS:
                validated_place_data = self._validate_and_prepare_place_data(map_slug)
                if validated_place_data["errors"]:
                    self._display_sync_validation_errors(validated_place_data["errors"])
                else:
                    place = self.landing.env["cm.place"].create(
                        validated_place_data["data"]
                    )
                    self._place_extra_data_setup(place)
        if mode == "update":
            for place in self.landing.map_place_ids:
                validated_place_data = self._validate_and_prepare_place_data(
                    place.map_id.slug_id
                )
                if validated_place_data["errors"]:
                    self._display_sync_validation_errors(validated_place_data["errors"])
                else:
                    place.write(validated_place_data["data"])
                    self._place_extra_data_setup(place)

    def _display_sync_validation_errors(self, errors):
        error_msg = ""
        for error in errors:
            error_msg += error + "\n"
        raise UserError(error_msg)

    def _place_extra_data_setup(self, place):
        # presenter metadata
        place.build_presenter_metadata_ids()
        # setup description
        self._setup_place_description(place)
        # setup external links
        self._setup_place_external_links(place)
        # apply translations
        self._apply_place_metadatas_translations(place)

    def _validate_and_prepare_place_data(self, map_slug):
        """
        Try to generate a place data dictionary and collect errors if they're
        @returns: dictionary with 'data' key as the dict to be used for place creation or update and 'errors' key to collect errors if they're
        """
        ret_dict = {
            "data": {
                "name": self.landing.name,
                "slug_id": self.landing.slug_id + "-" + map_slug,
                "landing_id": self.landing.id,
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
        map = self.landing.env["cm.map"].search([("slug_id", "=", map_slug)])
        if map:
            ret_dict["data"]["map_id"] = map.id
            ret_dict["data"]["company_id"] = map.company_id.id
        else:
            ret_dict["errors"].append(_("Map not found slug_id: {}").format(map_slug))
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
        # Related coordinator
        if self.landing.hierarchy_level == "community":
            coord_filter = False
            if self.landing.parent_landing_id:
                if self.landing.parent_landing_id.status == "publish":
                    coord_filter = (
                        self.landing.get_map_coordinator_filter_in_related_place()
                    )
            if coord_filter:
                ret_dict["data"]["filter_mids"].append((4, coord_filter.id))

        # Energy actions (Community active services)
        for eaction in self.landing.community_energy_action_ids:
            service_slug = MapClientConfig.MAPPING__LANDING_ENERGY_ACTIONS__MAP_FILTER[
                eaction.energy_action_id.xml_id
            ]
            if eaction.public_status == "published":
                place_service = filters.filtered(lambda r: r.slug_id == service_slug)
                if place_service:
                    ret_dict["data"]["filter_mids"].append((4, place_service.id))
                else:
                    ret_dict["errors"].append(
                        _("Place status filter not found slug_id: {}").format(
                            service_slug
                        )
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
                token,
                baseurl,
                self.landing.company_hierarchy_level_url(),
                self.landing.wp_landing_page_id,
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

    def _setup_landing_cooperator_buttons(self):
        defined_cooperator_buttons_ids = []
        existing_cooperator_buttons = self.landing.env[
            "landing.cooperator.button"
        ].search([("landing_page_id", "=", self.landing.id)])
        if self.landing.allow_new_members:
            defined_cooperator_buttons_ids.append(
                self._get_or_create_cooperator_button("become_cooperator").id
            )
            defined_cooperator_buttons_ids.append(
                self._get_or_create_cooperator_button("become_company_cooperator").id
            )
        else:
            cooperator_contact_button = self._get_or_create_cooperator_button("contact")
            if cooperator_contact_button:
                defined_cooperator_buttons_ids.append(cooperator_contact_button.id)
        # remove old external_links if needed
        for existing_cooperator_button in existing_cooperator_buttons:
            if (
                existing_cooperator_button.id not in defined_cooperator_buttons_ids
                and existing_cooperator_button.mode != "custom"
            ):
                existing_cooperator_button.unlink()

    def _setup_place_external_links(self, place):
        new_external_links_ids = []
        existing_external_links = self.landing.env["cm.place.external.link"].search(
            [("place_id", "=", place.id)]
        )
        for cooperator_button in self.landing.cooperator_button_ids:
            if cooperator_button.visibility == "visible":
                new_external_links_ids.append(
                    self._get_or_create_external_link(
                        place.id,
                        cooperator_button.name,
                        cooperator_button.url,
                        "_blank",
                        self.button_configs["yellow"].id,
                        cooperator_button.sort_order,
                        cooperator_button,
                    ).id
                )
        new_external_links_ids.append(
            self._landing_external_link(place, len(new_external_links_ids) - 1).id
        )
        # remove old external_links if needed
        for existing_external_link in existing_external_links:
            if existing_external_link.id not in new_external_links_ids:
                existing_external_link.unlink()

    def _get_or_create_cooperator_button(self, cooperator_mode):
        existing_cooperator_button = self.landing.env[
            "landing.cooperator.button"
        ].search(
            [("landing_page_id", "=", self.landing.id), ("mode", "=", cooperator_mode)]
        )
        if existing_cooperator_button:
            cooperator_button = existing_cooperator_button[0]
        else:
            cooperator_button = False
            create_dict = {
                "landing_page_id": self.landing.id,
                "mode": cooperator_mode,
                "name": self.landing.company_id.get_become_cooperator_button_label(
                    cooperator_mode, "ca_ES"
                ),
            }
            if cooperator_mode in ["become_cooperator", "become_company_cooperator"]:
                # become_cooperator scenario
                create_dict[
                    "url"
                ] = self.landing.company_id.get_become_cooperator_button_link(
                    cooperator_mode, "ca_ES"
                )
            else:
                # contact_us scenario
                if self.wp_landing_data["link"]:
                    create_dict[
                        "url"
                    ] = LandingClientConfig.COOPERATOR_BUTTON_URL_CONFIG[
                        "contact"
                    ].format(
                        landing_link=self.wp_landing_data["link"]
                    )
            if "url" in create_dict.keys():
                cooperator_button = self.landing.env[
                    "landing.cooperator.button"
                ].create(create_dict)
            # translations
            if cooperator_button:
                self._apply_cooperator_button_translations(cooperator_button)
        return cooperator_button

    def _apply_cooperator_button_translations(self, cooperator_button):
        self._become_cooperator_button_translation(cooperator_button, "en_US")
        for lang in LandingClientConfig.TRANSLATION_LANGS_MANAGED:
            self._become_cooperator_button_translation(cooperator_button, lang)

    def _become_cooperator_button_translation(self, cooperator_button, lang):
        mode = cooperator_button.mode
        if mode in ["become_cooperator", "become_company_cooperator"]:
            # become_cooperator scenario
            cooperator_button.with_context(lang=lang).write(
                {
                    "name": self.landing.company_id.get_become_cooperator_button_label(
                        mode, lang
                    ),
                    "url": self.landing.company_id.get_become_cooperator_button_link(
                        mode, lang
                    ),
                }
            )
        else:
            # contact_us scenario
            cooperator_button.with_context(lang=lang).write(
                {
                    "name": self.landing.company_id.get_become_cooperator_button_label(
                        mode, lang
                    ),
                }
            )
            if self.wp_landing_data["translations"]:
                lang_short = lang[:2]
                if lang_short == "en":
                    lang_short = "ca"  # odoo default "en" is on website "ca"
                if lang_short in self.wp_landing_data["translations"].keys():
                    cooperator_button.with_context(lang=lang).write(
                        {
                            "url": LandingClientConfig.COOPERATOR_BUTTON_URL_CONFIG[
                                "contact"
                            ].format(
                                landing_link=self.wp_landing_data["translations"][
                                    lang_short
                                ]
                            ),
                        }
                    )

    def _get_or_create_external_link(
        self,
        place_id,
        name,
        url,
        target,
        button_color_config_id,
        sort_order,
        cooperator_button=False,
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
            external_link = existing_external_links[0]
        else:
            external_link = self.landing.env["cm.place.external.link"].create(
                {
                    "place_id": place_id,
                    "name": name,
                    "url": url,
                    "target": target,
                    "button_color_config_id": button_color_config_id,
                }
            )
        if cooperator_button:
            # translations from cooperator button translations
            for lang in LandingClientConfig.TRANSLATION_LANGS_MANAGED:
                external_link.with_context(lang=lang).write(
                    {
                        "name": cooperator_button.with_context(lang=lang).name,
                        "url": cooperator_button.with_context(lang=lang).url,
                    }
                )
        return external_link

    def _landing_external_link(self, place, sort_order):
        external_link = self._get_or_create_external_link(
            place.id,
            MapClientConfig.MAPPING__EXTERNAL_LINK__LANDING__LINK_LABEL["ca_ES"],
            self.wp_landing_data["link"],
            "_top",
            self.button_configs["green"].id,
            sort_order,
        )
        # setup social sahreable url for better sharing
        place.write({"social_shareable_url": self.wp_landing_data["link"]})
        # Translations
        for lang in LandingClientConfig.TRANSLATION_LANGS_MANAGED:
            external_link.with_context(lang=lang).write(
                {
                    "name": MapClientConfig.MAPPING__EXTERNAL_LINK__LANDING__LINK_LABEL[
                        lang
                    ],
                }
            )
            if self.wp_landing_data["translations"]:
                lang_short = lang[:2]
                if lang_short in self.wp_landing_data["translations"].keys():
                    place.with_context(lang=lang).write(
                        {
                            "social_shareable_url": self.wp_landing_data[
                                "translations"
                            ][lang_short]
                        }
                    )
                    external_link.with_context(lang=lang).write(
                        {"url": self.wp_landing_data["translations"][lang_short]}
                    )
        return external_link

    def _apply_place_metadatas_translations(self, place):
        for lang in LandingClientConfig.TRANSLATION_LANGS_MANAGED:
            # description
            self._apply_place_metadata_translation(
                place.id,
                MapClientConfig.MAPPING__OPEN_PLACE_DESCRIPTION_META_KEY,
                self.landing.with_context(lang=lang).short_description,
                lang,
            )
            # place social headlines
            self._apply_place_metadata_translation(
                place.id,
                MapClientConfig.MAPPING__OPEN_PLACE_SOCIAL_HEADLINE_META_KEY,
                MapClientConfig.MAPPING__OPEN_PLACE_SOCIAL_HEADLINE_TRANSLATION[lang],
                lang,
            )

    def _apply_place_metadata_translation(self, place_id, meta_key, trans_value, lang):
        related_meta = self.landing.env["cm.place.presenter.metadata"].search(
            [("place_id", "=", place_id), ("key", "=", meta_key)]
        )
        if related_meta:
            related_meta.with_context(lang=lang).write({"value": trans_value})
