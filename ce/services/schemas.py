def boolean_validator(field, value, error):
    if value and value not in ["true", "false"]:
        error(field, "Must be a boolean value: true or false")

S_CRM_LEAD_RETURN_CREATE = {
    "id": {"type": "integer"}
}

S_CRM_LEAD_CREATE = {
    "partner_name": {"type": "string"},
    "source_id": {"type": "integer"},
    "email_from": {"type": "string"},
    "phone": {"type": "string"},
    "odoo_company_id": {"type": "integer"},
}
