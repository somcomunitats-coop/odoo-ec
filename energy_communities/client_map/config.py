class LandingClientConfig:
    TRANSLATION_LANGS_MANAGED = ["ca_ES", "es_ES", "eu_ES"]
    COOPERATOR_BUTTON_URL_CONFIG = {
        "become_cooperator": "{base_url}/{lang}/become_cooperator?odoo_company_id={odoo_company_id}",
        "become_company_cooperator": "{base_url}/{lang}/become_company_cooperator?odoo_company_id={odoo_company_id}",
        "contact": "{landing_link}#contacte",
    }
    COOPERATOR_BUTTON_LABEL_CONFIG = {
        "become_cooperator": {
            "en_US": "Fer-me soci/a com a ciutadania",
            "ca_ES": "Fer-me soci/a com a ciutadania",
            "es_ES": "Hazte socio/a como ciudadania",
            "eu_ES": "Egin zaitez bazkide herritar gisa",
        },
        "become_company_cooperator": {
            "en_US": "Fer-me soci/a com a empresa",
            "ca_ES": "Fer-me soci/a com a empresa",
            "es_ES": "Hazte socio/a como empresa",
            "eu_ES": "Egin zaitez bazkide enpresa gisa",
        },
        "contact": {
            "en_US": "Posa-t’hi en contacte",
            "ca_ES": "Posa-t’hi en contacte",
            "es_ES": "Ponte en contacto",
            "eu_ES": "Jarri harremanetan",
        },
    }


class MapClientConfig:
    # mapping between landings params and place params
    MAPPING__INSTANCE_ID = 1
    MAPPING__LANDING_ENERGY_ACTIONS__MAP_FILTER = {
        "energy_communities.energy_action_common_generation": "generacio-renovable-comunitaria",
        "energy_communities.energy_action_energy_efficiency": "eficiencia-energetica",
        "energy_communities.energy_action_sustainable_mobility": "mobilitat-sostenible",
        "energy_communities.energy_action_citizen_education": "formacio-ciutadana",
        "energy_communities.energy_action_thermal_energy": "energia-termica-i-climatitzacio",
        "energy_communities.energy_action_collective_purchases": "compres-col-lectives",
        "energy_communities.energy_action_renewable_energy": "subministrament-d-energia-100-renovable",
        "energy_communities.energy_action_aggregate_demand": "agregacio-i-flexibilitat-de-la-demanda",
    }
    MAPPING__MAP = "campanya"
    MAPPING__MAPS = ["campanya", "sumate-goiener", "sumate-energetica", "sumate-ecooo"]
    MAPPING__LANDING_COMMUNITY_STATUS__MAP_FILTER = {"open": "oberta"}
    MAPPING__LANDING_STATUS__MAP_PLACE_STATUS = {
        "draft": "draft",
        "publish": "published",
    }
    MAPPING__LANDING_COMMUNITY_TYPE__MAP_CATEGORY = {
        "citizen": "ciutadania",
        "industrial": "industrial",
    }
    MAPPING__LANDING_COMMUNITY_STATUS__MAP_PRESENTER = {"open": "CE Oberta"}
    MAPPING__OPEN_PLACE_DESCRIPTION_META_KEY = "po2_description"
    MAPPING__OPEN_PLACE_SOCIAL_HEADLINE_META_KEY = "po2_social_headline"
    MAPPING__OPEN_PLACE_SOCIAL_HEADLINE_ORIGINAL = "<div class='flex justify-center align-center text-center'><p class='font-semibold text-white'>Comparteix i fem créixer la Comunitat Energètica</p></div>"
    MAPPING__OPEN_PLACE_SOCIAL_HEADLINE_TRANSLATION = {
        "en_US": "<div class='flex justify-center align-center text-center'><p class='font-semibold text-white'>Comparteix i fem créixer la Comunitat Energètica</p></div>",
        "ca_ES": "<div class='flex justify-center align-center text-center'><p class='font-semibold text-white'>Comparteix i fem créixer la Comunitat Energètica</p></div>",
        "es_ES": "<div class='flex justify-center align-center text-center'><p class='font-semibold text-white'>Comparte y hagamos crecer la Comunidad Energética</p></div>",
        "eu_ES": "<div class='flex justify-center align-center text-center'><p class='font-semibold text-white'>Partekatu eta lagundu hazten energia-komunitateari</p></div>",
    }
    MAPPING__EXTERNAL_LINK__BECOME_COOPERATOR__LINK_LABEL = {
        "en_US": "Fes-te'n soci/a",
        "ca_ES": "Fes-te'n soci/a",
        "es_ES": "Hazte socio/a",
        "eu_ES": "Bazkide bihurtu",
    }
    MAPPING__EXTERNAL_LINK__CONTACT__LINK_LABEL = {
        "en_US": "Posa-t'hi en contacte",
        "ca_ES": "Posa-t'hi en contacte",
        "es_ES": "Ponte en contacto",
        "eu_ES": "Jarri harremanetan",
    }
    MAPPING__EXTERNAL_LINK__LANDING__LINK_LABEL = {
        "en_US": "Veure pàgina de la Comunitat",
        "ca_ES": "Veure pàgina de la Comunitat",
        "es_ES": "Ver página de la Comunidad",
        "eu_ES": "Ikus Komunitatearen orria",
    }
    MAPPING__BUTTON_COLOR_CONFIG_NAME = {
        "green": "Coorporate green dark button",
        "yellow": "Coorporate yellow button",
    }
    FILTER_COLOR_CONFIG = {
        "marker_color": "#8EC23A",
        "marker_text_color": "#FFFFFF",
        "marker_bg_color": "#AEE04C",
        "marker_border_color": "transparent",
    }
