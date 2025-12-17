from unittest.mock import patch

import requests

from odoo import _
from odoo.tests import common, tagged

from ..client_map.config import LandingClientConfig

TESTED_LANGS = ["ca_ES", "es_ES", "eu_ES"]


@tagged("-at_install", "post_install")
class TestLandingPlace(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.landing = self.env.ref(
            "energy_communities.landing_page_coordinator_company_demo_1"
        )

    @property
    def wp_landing_page_response(self):
        return {
            "link": "https://test.com",
            "translations": {
                "ca": "https://test.com",
                "es": "https://test.com/es",
                "eu": "https://test.com/eu",
            },
        }

    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation(self, patcher):
        patcher.return_value = self.wp_landing_page_response
        # given a landing without places
        places = self.env["cm.place"].search([("landing_id", "=", self.landing.id)])
        self.assertFalse(bool(places))
        # when we create related places
        self.landing.action_create_landing_place()
        # places are created
        places = self.env["cm.place"].search([("landing_id", "=", self.landing.id)])
        self.assertTrue(bool(places))
        self.assertEqual(len(places), 4)

    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_cooperator_buttons_allow_new_members(
        self, patcher
    ):
        patcher.return_value = self.wp_landing_page_response
        # given a landing without coop buttons
        self.assertFalse(bool(self.landing.cooperator_button_ids))
        # when we create related places
        self.landing.action_create_landing_place()
        # cooperator buttons are properly created
        self.assertTrue(bool(self.landing.cooperator_button_ids))
        self.assertEqual(len(self.landing.cooperator_button_ids), 3)

    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_cooperator_buttons_allow_dont_new_members(
        self, patcher
    ):
        patcher.return_value = self.wp_landing_page_response
        # given a landing without coop buttons and without allowing new members
        self.landing.company_id.write({"allow_new_members": False})
        self.assertFalse(bool(self.landing.cooperator_button_ids))
        # when we create related places
        self.landing.action_create_landing_place()
        # cooperator buttons are properly created
        self.assertTrue(bool(self.landing.cooperator_button_ids))
        self.assertEqual(len(self.landing.cooperator_button_ids), 2)

    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_cooperator_buttons_data_allow_new_members(
        self, patcher
    ):
        patcher.return_value = self.wp_landing_page_response
        # given a landing without coop buttons
        # when we create related places
        self.landing.action_create_landing_place()
        # cooperator buttons are properly configured
        # become cooperator
        button = self.env["landing.cooperator.button"].search(
            [
                ("mode", "=", "become_cooperator"),
                ("landing_page_id", "=", self.landing.id),
            ]
        )
        self.assertEqual(len(button), 1)
        self._assert_button_data(button, "map_landing")
        # become company cooperator
        button = self.env["landing.cooperator.button"].search(
            [
                ("mode", "=", "become_company_cooperator"),
                ("landing_page_id", "=", self.landing.id),
            ]
        )
        self.assertEqual(len(button), 1)
        self._assert_button_data(button, "map_landing")
        # landing_page
        button = self.env["landing.cooperator.button"].search(
            [("mode", "=", "landing_page"), ("landing_page_id", "=", self.landing.id)]
        )
        self.assertEqual(len(button), 1)
        self._assert_button_data(button, "map")

    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_cooperator_buttons_data_dont_allow_new_members(
        self, patcher
    ):
        patcher.return_value = self.wp_landing_page_response
        # given a landing without coop buttons and without allowing new members
        self.landing.company_id.write({"allow_new_members": False})
        # when we create related places
        self.landing.action_create_landing_place()
        # cooperator buttons are properly configured
        # contact
        button = self.env["landing.cooperator.button"].search(
            [("mode", "=", "contact"), ("landing_page_id", "=", self.landing.id)]
        )
        self.assertEqual(len(button), 1)
        self._assert_button_data(button, "map_landing")
        # landing_page
        button = self.env["landing.cooperator.button"].search(
            [("mode", "=", "landing_page"), ("landing_page_id", "=", self.landing.id)]
        )
        self.assertEqual(len(button), 1)
        self._assert_button_data(button, "map")

    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_cooperator_buttons_place_external_links_allow_new_members(
        self, patcher
    ):
        patcher.return_value = self.wp_landing_page_response
        # given a landing without coop buttons
        # when we create related places
        self.landing.action_create_landing_place()
        # created buttons and place external link match
        places = self.env["cm.place"].search([("landing_id", "=", self.landing.id)])
        for place in places:
            self._assert_landing_button_map_external_link_consistency(place)

    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_cooperator_buttons_place_external_links_dont_allow_new_members(
        self, patcher
    ):
        patcher.return_value = self.wp_landing_page_response
        # given a landing without coop buttons and without allowing new members
        self.landing.company_id.write({"allow_new_members": False})
        # when we create related places
        self.landing.action_create_landing_place()
        # created buttons and place external link match
        places = self.env["cm.place"].search([("landing_id", "=", self.landing.id)])
        for place in places:
            self._assert_landing_button_map_external_link_consistency(place)

    @patch(
        "odoo.addons.energy_communities.models.landing_page.LandingPage._update_wordpress"
    )
    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_cooperator_buttons_inmutable(
        self, wordpress_landing_data_patcher, wordpress_update_patcher
    ):
        wordpress_landing_data_patcher.return_value = self.wp_landing_page_response
        wordpress_update_patcher.return_value = None
        # given a landing without coop buttons
        # when we create related places
        self.landing.action_create_landing_place()
        # and we modify some coop buttons
        for index, coop_button in enumerate(self.landing.cooperator_button_ids):
            coop_button.write(
                {
                    "name": "modified base name {}".format(index),
                    "url": "https://modified_base_url.{}.extension".format(index),
                }
            )
            for lang in TESTED_LANGS:
                coop_button.with_context(lang=lang).write(
                    {
                        "name": "modified base name {} with lang {}".format(
                            index, lang
                        ),
                        "url": "https://modified_base_url.{}.extension.{}".format(
                            index, lang
                        ),
                    }
                )
        # if we update map place
        self.landing.action_update_public_data()
        # buttons remain as default ones
        for coop_button in self.landing.cooperator_button_ids.filtered(
            lambda record: record.mode != "landing_page"
        ):
            self._assert_button_data(coop_button, "map_landing")
        for coop_button in self.landing.cooperator_button_ids.filtered(
            lambda record: record.mode == "landing_page"
        ):
            self._assert_button_data(coop_button, "map")
        # and buttons are properly propagated
        places = self.env["cm.place"].search([("landing_id", "=", self.landing.id)])
        for place in places:
            self._assert_landing_button_map_external_link_consistency(place)

    @patch(
        "odoo.addons.energy_communities.models.landing_page.LandingPage._update_wordpress"
    )
    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_custom_cooperator_buttons(
        self, wordpress_landing_data_patcher, wordpress_update_patcher
    ):
        wordpress_landing_data_patcher.return_value = self.wp_landing_page_response
        wordpress_update_patcher.return_value = None
        # given a landing without coop buttons
        # when we create related places
        self.landing.action_create_landing_place()
        # we have only default coop buttons
        self.assertEqual(len(self.landing.cooperator_button_ids), 3)
        for coop_button in self.landing.cooperator_button_ids.filtered(
            lambda record: record.mode != "landing_page"
        ):
            self._assert_button_data(coop_button, "map_landing")
        for coop_button in self.landing.cooperator_button_ids.filtered(
            lambda record: record.mode == "landing_page"
        ):
            self._assert_button_data(coop_button, "map")
        # if we create a custom button
        custom_button = self.env["landing.cooperator.button"].create(
            {
                "name": "custom button",
                "url": "custom_url.extension",
                "landing_page_id": self.landing.id,
                "sort_order": 3,
            }
        )
        for lang in TESTED_LANGS:
            custom_button.with_context(lang=lang).write(
                {
                    "name": "custom button {}".format(lang),
                    "url": "custom_url.{}.extension".format(lang),
                }
            )
        self.assertEqual(custom_button.mode, "custom")
        self.assertEqual(custom_button.visibility, "map_landing")
        self.assertEqual(len(self.landing.cooperator_button_ids), 4)
        # if we update map place
        self.landing.action_update_public_data()
        self.assertEqual(len(self.landing.cooperator_button_ids), 4)
        # buttons are properly propagated
        places = self.env["cm.place"].search([("landing_id", "=", self.landing.id)])
        for place in places:
            self._assert_landing_button_map_external_link_consistency(place)

    @patch(
        "odoo.addons.energy_communities.models.landing_page.LandingPage._update_wordpress"
    )
    @patch(
        "odoo.addons.energy_communities.client_map.resources.landing_cmplace.LandingCmPlace._get_wp_landing_data"
    )
    def test__map_place_creation_landing_hidden_buttons(
        self, wordpress_landing_data_patcher, wordpress_update_patcher
    ):
        wordpress_landing_data_patcher.return_value = self.wp_landing_page_response
        wordpress_update_patcher.return_value = None
        # given a landing without coop buttons
        # when we create related places
        self.landing.action_create_landing_place()
        # we have only default coop buttons
        self.assertEqual(len(self.landing.cooperator_button_ids), 3)
        for coop_button in self.landing.cooperator_button_ids.filtered(
            lambda record: record.mode != "landing_page"
        ):
            self._assert_button_data(coop_button, "map_landing")
        for coop_button in self.landing.cooperator_button_ids.filtered(
            lambda record: record.mode == "landing_page"
        ):
            self._assert_button_data(coop_button, "map")
        # if we hide a button
        self.landing.cooperator_button_ids[0].write({"visibility": "hidden"})
        # and we update map place
        self.landing.action_update_public_data()
        # buttons are properly propagated
        self.assertEqual(len(self.landing.cooperator_button_ids), 3)
        places = self.env["cm.place"].search([("landing_id", "=", self.landing.id)])
        for place in places:
            self.assertEqual(len(place.external_link_ids), 2)

    def _assert_landing_button_map_external_link_consistency(self, place):
        for index, ext_link in enumerate(place.external_link_ids):
            self.assertEqual(
                ext_link.name, self.landing.cooperator_button_ids[index].name
            )
            self.assertEqual(
                ext_link.url, self.landing.cooperator_button_ids[index].url
            )
            for lang in TESTED_LANGS:
                self.assertEqual(
                    ext_link.with_context(lang=lang).name,
                    self.landing.cooperator_button_ids[index]
                    .with_context(lang=lang)
                    .name,
                )
                self.assertEqual(
                    ext_link.with_context(lang=lang).url,
                    self.landing.cooperator_button_ids[index]
                    .with_context(lang=lang)
                    .url,
                )
            mode = self.landing.cooperator_button_ids[index].mode
            if mode in [
                "become_cooperator",
                "become_company_cooperator",
                "contact",
                "custom",
            ]:
                self.assertEqual(ext_link.target, "_blank")
                self.assertEqual(
                    ext_link.button_color_config_id,
                    self.env.ref("energy_communities.map_color_config_demo_2"),
                )
            if mode == "landing_page":
                self.assertEqual(ext_link.target, "_top")
                self.assertEqual(
                    ext_link.button_color_config_id,
                    self.env.ref("energy_communities.map_color_config_demo_1"),
                )
                self.assertEqual(
                    place.social_shareable_url,
                    self.landing.cooperator_button_ids[index].url,
                )
                for lang in TESTED_LANGS:
                    self.assertEqual(
                        place.with_context(lang=lang).social_shareable_url,
                        self.landing.cooperator_button_ids[index]
                        .with_context(lang=lang)
                        .url,
                    )

    def _assert_button_data(self, button, expected_visibility):
        # visibility
        self.assertEqual(button.visibility, expected_visibility)
        # base name
        self.assertEqual(
            button.name,
            LandingClientConfig.COOPERATOR_BUTTON_LABEL_CONFIG[button.mode]["ca_ES"],
        )
        for lang in TESTED_LANGS:
            # name values
            self.assertEqual(
                button.with_context(lang=lang).name,
                LandingClientConfig.COOPERATOR_BUTTON_LABEL_CONFIG[button.mode][lang],
            )
            # url values
            if button.mode in ["become_cooperator", "become_company_cooperator"]:
                self.assertEqual(
                    button.url,
                    LandingClientConfig.COOPERATOR_BUTTON_URL_CONFIG[
                        button.mode
                    ].format(
                        base_url=self.env["ir.config_parameter"].get_param(
                            "web.base.url"
                        ),
                        lang="en_US",
                        odoo_company_id=self.landing.company_id.id,
                    ),
                )
                self.assertEqual(
                    button.with_context(lang=lang).url,
                    LandingClientConfig.COOPERATOR_BUTTON_URL_CONFIG[
                        button.mode
                    ].format(
                        base_url=self.env["ir.config_parameter"].get_param(
                            "web.base.url"
                        ),
                        lang=lang,
                        odoo_company_id=self.landing.company_id.id,
                    ),
                )
            if button.mode == "landing_page":
                self.assertEqual(button.url, self.wp_landing_page_response["link"])
                self.assertEqual(
                    button.with_context(lang=lang).url,
                    self.wp_landing_page_response["translations"][lang[:2]],
                )
            if button.mode == "contact":
                self.assertEqual(
                    button.url,
                    LandingClientConfig.COOPERATOR_BUTTON_URL_CONFIG["contact"].format(
                        landing_link=self.wp_landing_page_response["link"]
                    ),
                )
                self.assertEqual(
                    button.with_context(lang=lang).url,
                    LandingClientConfig.COOPERATOR_BUTTON_URL_CONFIG["contact"].format(
                        landing_link=self.wp_landing_page_response["translations"][
                            lang[:2]
                        ]
                    ),
                )
