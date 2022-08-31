def boolean_validator(field, value, error):
    if value and value not in ["true", "false"]:
        error(field, "Must be a boolean value: true or false")

S_SET_PERMS_REQUEST_GET = {
    "company_id": {"type": "string", "required": True},
    "user_id": {"type": "string", "required": True},
    "target_company_id": {"type": "string", "required": True},
    "target_user_id": {"type": "string", "required": True},
    "new_role": {"type": "string", "required": True},
}

S_SET_PERMS_REQUEST_RETURN = {
    "message": {"type": "boolean", "required": True},
}

S_CRM_LEAD_RETURN_CREATE = {
    "id": {"type": "integer"},
}

S_CRM_LEAD_CREATE = {
    "partner_name": {"type": "string"},
    "partner_email": {"type": "string"},
    "partner_phone": {"type": "string"},
    "partner_full_address": {"type": "string"},
    "partner_city": {"type": "string"},
    "partner_zip": {"type": "string"},
    "odoo_company_id": {"type": "integer"},
    "source_xml_id": {"type": "string"},
    "tag_ids": {
        "type": "list",
        "schema": {
            "type": "integer",
        }
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
            "payment_info": {
                "type": "dict",
                "schema": {
                    "iban": {"type": "string"},
                    "sepa_accepted": {"type": "boolean"},
                }
            },
            "suscriptions": {
                "type": "dict",
                "schema": {
                    "community_news": {"type": "boolean"},
                }
            },
            "odoo_res_users_id": {"type": "integer"},
            "odoo_res_partner_id": {"type": "integer"},
        }
    }
}

S_PROFILE_PUT = {
    "lang": {"type": "string", "required": True, "empty": False}
}

S_PROFILE_RETURN_PUT = S_PROFILE_RETURN_GET

S_COMMUNITY_MEMBER = {
    "name": {"type": "string", "required": True, "empty": False},
    "rol": {"type": "string", "required": True},
    "email": {"type": "string", "required": True},
}

S_COMMUNITY_MEMBERS_RETURN_GET = {
    "members": {
        "type": "list",
        "schema": {
            "type": "dict",
            "schema": S_COMMUNITY_MEMBER
        }
    }
}
