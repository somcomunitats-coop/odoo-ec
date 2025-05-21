S_ENERGY_ACTION = {
    "id": {"type": "integer"},
    "name": {"type": "string"},
    "ext_id": {"type": "string"},
}

S_COOPERATOR_BUTTON = {
    "name": {"type": "string"},
    "url": {"type": "string"},
}

S_LANDING_PAGE_GET_RETURN = {
    "landing": {
        "type": "dict",
        "schema": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "title": {"type": "string"},
            "company_id": {"type": "integer"},
            "odoo_company_id": {"type": "integer"},
            "wp_landing_page_id": {"type": "integer"},
            "status": {"type": "string"},
            "community_type": {"type": "string"},
            "community_secondary_type": {"type": "string"},
            "legal_form": {"type": "string"},
            "community_status": {"type": "string"},
            "allow_new_members": {"type": "boolean"},
            "number_of_members": {"type": "integer"},
            "external_website_link": {"type": "string"},
            "show_web_link_on_header": {"type": "boolean"},
            "show_newsletter_form": {"type": "boolean"},
            "twitter_link": {"type": "string"},
            "instagram_link": {"type": "string"},
            "telegram_link": {"type": "string"},
            "energy_actions": {
                "type": "list",
                "schema": {"type": "dict", "schema": S_ENERGY_ACTION},
            },
            "company_logo": {"type": "string"},
            "company_logo_write_date": {"type": "string"},
            "primary_image_file": {"type": "string"},
            "primary_image_file_write_date": {"type": "string"},
            "secondary_image_file": {"type": "string"},
            "secondary_image_file_write_date": {"type": "string"},
            "short_description": {"type": "string"},
            "long_description": {"type": "string"},
            "why_become_cooperator": {"type": "string"},
            "become_cooperator_process": {"type": "string"},
            "cooperator_buttons": {
                "type": "list",
                "schema": {"type": "dict", "schema": S_COOPERATOR_BUTTON},
            },
            "map_reference": {"type": "string"},
            "street": {"type": "string"},
            "postal_code": {"type": "string"},
            "city": {"type": "string"},
            "slug_id": {"type": "string"},
            "display_map": {"type": "boolean"},
            "awareness_services": {"type": "string"},
            "design_services": {"type": "string"},
            "management_services": {"type": "string"},
        },
    }
}
