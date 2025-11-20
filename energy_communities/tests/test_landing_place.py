from unittest.mock import patch

import requests

from odoo import _
from odoo.tests import common, tagged

from ..client_map.config import LandingClientConfig


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
        self._assert_button_data(button)
        # become company cooperator
        button = self.env["landing.cooperator.button"].search(
            [
                ("mode", "=", "become_company_cooperator"),
                ("landing_page_id", "=", self.landing.id),
            ]
        )
        self.assertEqual(len(button), 1)
        self._assert_button_data(button)
        # landing_page
        button = self.env["landing.cooperator.button"].search(
            [("mode", "=", "landing_page"), ("landing_page_id", "=", self.landing.id)]
        )
        self.assertEqual(len(button), 1)
        self._assert_button_data(button)

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
        self._assert_button_data(button)
        # landing_page
        button = self.env["landing.cooperator.button"].search(
            [("mode", "=", "landing_page"), ("landing_page_id", "=", self.landing.id)]
        )
        self.assertEqual(len(button), 1)
        self._assert_button_data(button)

    def _assert_button_data(self, button):
        # visibility
        self.assertEqual(button.visibility, "visible")
        # base name
        self.assertEqual(
            button.name,
            LandingClientConfig.COOPERATOR_BUTTON_LABEL_CONFIG[button.mode]["ca_ES"],
        )
        for lang in ["ca_ES", "es_ES", "eu_ES"]:
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
