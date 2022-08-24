def boolean_validator(field, value, error):
    if value and value not in ["true", "false"]:
        error(field, "Must be a boolean value: true or false")


S_CRM_LEAD_RETURN_CREATE = {
    "id": {"type": "integer"},
}
S_CRM_LEAD_CREATE = {
    "partner_name": {"type": "string"},
    "source_id": {"type": "integer"},
    "email_from": {"type": "string"},
    "phone": {"type": "string"},
    "odoo_company_id": {"type": "integer"},
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
