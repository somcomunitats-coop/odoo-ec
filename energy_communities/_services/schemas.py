def boolean_validator(field, value, error):
    if value and value not in ["true", "false"]:
        error(field, "Must be a boolean value: true or false")


def ce_state_validator(field, value, error):
    if value and value not in ["active", "on_building"]:
        error(field, "Must be 'active' or 'on_building'")


# S_CRM_LEAD_RETURN_CREATE = {
#     "id": {"type": "integer"},
# }

# S_CRM_LEAD_CREATE = {
#     "partner_name": {"type": "string"},
#     "partner_email": {"type": "string"},
#     "partner_phone": {"type": "string"},
#     "partner_full_address": {"type": "string"},
#     "partner_city": {"type": "string"},
#     "partner_zip": {"type": "string"},
#     "odoo_company_id": {"type": "integer"},
#     "source_xml_id": {"type": "string"},
#     "tag_ids": {
#         "type": "list",
#         "schema": {
#             "type": "integer",
#         },
#     },
#     "partner_description": {"type": "string"},
# }

# S_CRM_LEAD_CREATE_ALTA_CE = {
#     "partner_name": {"type": "string", "required": True},
#     "partner_description": {"type": "string", "required": True},
#     "partner_full_address": {"type": "string", "required": True},
#     "partner_zip": {"type": "string", "required": True},
#     "partner_city": {"type": "string", "required": True},
#     "partner_state": {"type": "string", "required": True},
#     "partner_qty_members": {"type": "integer", "required": True},
#     "partner_legal_state": {"type": "string", "check_with": ce_state_validator},
#     "tag_ids": {
#         "type": "list",
#         "schema": {
#             "type": "integer",
#         },
#         "required": True,
#     },
#     "partner_foundation_date": {"type": "string"},
#     "partner_vat": {"type": "string"},
#     "partner_comments": {"type": "string"},
#     "partner_firstname": {"type": "string", "required": True},
#     "partner_lastname": {"type": "string", "required": True},
#     "partner_email": {"type": "string", "required": True},
#     "partner_phone": {"type": "string", "required": True},
#     "contact2_firstname": {"type": "string"},
#     "contact2_lastname": {"type": "string"},
#     "contact2_email": {"type": "string"},
#     "contact2_mobile": {"type": "string"},
#     "odoo_company_id": {"type": "integer", "required": True},
#     "source_xml_id": {"type": "string", "required": True},
#     "partner_map_place_form_url": {"type": "string", "required": False},
#     "partner_language": {"type": "string"},
# }

S_PROFILE_COMMUNITY_GET = {
    "type": "dict",
    "schema": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "role": {"type": "string"},
        "public_web_landing_url": {"type": "string"},
        "keycloak_odoo_login_url": {"type": "string"},
        "payment_info": {
            "type": "dict",
            "schema": {
                "iban": {"type": "string"},
                "sepa_accepted": {"type": "boolean"},
            },
        },
    },
}

S_PROFILE_RETURN_GET = {
    "profile": {
        "type": "dict",
        "schema": {
            "keycloak_id": {"type": "string"},
            "name": {"type": "string"},
            "surname": {"type": "string"},
            "birth_date": {"type": "string"},
            "gender": {"type": "string"},
            "vat": {"type": "string"},
            "contact_info": {
                "type": "dict",
                "schema": {
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "street": {"type": "string"},
                    "postal_code": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "country": {"type": "string"},
                },
            },
            "language": {"type": "string"},
            "communities": {"type": "list", "schema": S_PROFILE_COMMUNITY_GET},
            "suscriptions": {
                "type": "dict",
                "schema": {
                    "community_news": {"type": "boolean"},
                },
            },
            "odoo_res_users_id": {"type": "integer"},
            "odoo_res_partner_id": {"type": "integer"},
        },
    }
}

S_MEMBER_PROFILE_RETURN_GET = {
    "member": {
        "type": "dict",
        "schema": {
            "keycloak_id": {"type": "string"},
            "name": {"type": "string"},
            "role": {"type": "string"},
            "email": {"type": "string"},
        },
    }
}

S_PROFILE_PUT = {"language": {"type": "string", "required": True, "empty": False}}

S_MEMBER_PROFILE_PUT = {"role": {"type": "string", "required": True, "empty": False}}

S_PROFILE_RETURN_PUT = S_PROFILE_RETURN_GET

S_MEMBER_PROFILE_RETURN_PUT = S_MEMBER_PROFILE_RETURN_GET


S_COMMUNITY_MEMBER = {
    "name": {"type": "string", "required": True, "empty": False},
    "role": {"type": "string", "required": True},
    "email": {"type": "string", "required": True},
    "keycloak_id": {"type": "string"},
}

S_COMMUNITY_MEMBERS_RETURN_GET = {
    "members": {
        "type": "list",
        "schema": {"type": "dict", "schema": S_COMMUNITY_MEMBER},
    }
}

S_COMMUNITY_SERVICE = {
    "id": {"type": "integer"},
    "name": {"type": "string"},
    "ext_id": {"type": "string"},
}

S_ENERGY_ACTION = {
    "id": {"type": "integer"},
    "name": {"type": "string"},
    "ext_id": {"type": "string"},
}

S_COMMUNITY_RETURN_GET = {
    "community": {
        "type": "dict",
        "schema": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "birth_date": {"type": "string"},
            "members": {
                "type": "list",
                "schema": {"type": "dict", "schema": S_COMMUNITY_MEMBER},
            },
            "contact_info": {
                "type": "dict",
                "schema": {
                    "street": {"type": "string"},
                    "postal_code": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "country": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "telegram": {"type": "string"},
                },
            },
            "active_services": {
                "type": "list",
                "schema": {"type": "dict", "schema": S_COMMUNITY_SERVICE},
            },
            "allow_new_members": {"type": "boolean"},
            "public_web_landing_url": {"type": "string"},
            "keycloak_odoo_login_url": {"type": "string"},
        },
    }
}
S_LANDING_PAGE_CREATE = {
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
            "twitter_link": {"type": "string"},
            "instagram_link": {"type": "string"},
            "telegram_link": {"type": "string"},
            "community_active_services": {
                "type": "list",
                "schema": {"type": "dict", "schema": S_COMMUNITY_SERVICE},
            },
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
S_LANDING_PAGE_GET = {
    "landing_id": {"type": "integer", "required": True, "empty": False}
}
