class MapClientConfig:
    # mapping between landings params and place params
    MAPPING__INSTANCE_ID = 1
    MAPPING__LANDING_ACTIVE_SERVICES__MAP_FILTER = {
        "energy_communities.ce_tag_common_generation": "generacio-renovable-comunitaria",
        "energy_communities.ce_tag_energy_efficiency": "eficiencia-energetica",
        "energy_communities.ce_tag_sustainable_mobility": "mobilitat-sostenible",
        "energy_communities.ce_tag_citizen_education": "formacio-ciutadana",
        "energy_communities.ce_tag_thermal_energy": "energia-termica-i-climatitzacio",
        "energy_communities.ce_tag_collective_purchases": "compres-col-lectives",
        "energy_communities.ce_tag_renewable_energy": "subministrament-d-energia-100-renovable",
        "energy_communities.ce_tag_aggregate_demand": "agregacio-i-flexibilitat-de-la-demanda",
    }
    MAPPING__MAP = "campanya"
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
        "es_ES": "<div class='flex justify-center align-center text-center'><p class='font-semibold text-white'>Comparte y hagamos crecer la Comunidad Energética</p></div>"
    }
    MAPPING__EXTERNAL_LINK__BECOME_COOPERATOR__LINK_LABEL = {
        "ca_ES": "Fes-te'n soci/a",
        "es_ES": "Hazte socio/a",
        "eu_ES": "Bazkide bihurtu",
    }
    MAPPING__EXTERNAL_LINK__CONTACT__LINK_LABEL = {
        "ca_ES": "Posa-t'hi en contacte",
        "es_ES": "Ponte en contacto",
        "eu_ES": "Jarri harremanetan",
    }
    MAPPING__EXTERNAL_LINK__LANDING__LINK_LABEL = {
        "ca_ES": "Veure pàgina de la Comunitat",
        "es_ES": "Ver página de la Comunidad",
        "eu_ES": "Ikus Komunitatearen orria",
    }
    MAPPING__BUTTON_COLOR_CONFIG_NAME = {
        "green": "Coorporate green dark button",
        "yellow": "Coorporate yellow button",
    }
