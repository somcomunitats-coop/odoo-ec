def boolean_validator(field, value, error):
    if value and value not in ["true", "false"]:
        error(field, "Must be a boolean value: true or false")

S_CRM_LEAD_RETURN_CREATE = {
    "id": {"type": "integer"}
}

S_CRM_LEAD_CREATE = {
    "partner_name": {"type": "string"},
    "partner_email": {"type": "string"},
    "partner_phone": {"type": "string"},
    "partner_full_address": {"type": "string"},
    "partner_city": {"type": "string"},
    "partner_zip": {"type": "string"},
    "odoo_company_id": {"type": "integer"},
    "source_xml_id": {"type": "integer"},
    "tag_ids": {
        "type": "list",
        "schema": {
            "type": "integer",
        }
    },

}
