# Copyright 2020 Coop IT Easy SCRL fs
#   Robin Keunen <robin@coopiteasy.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _
from odoo.fields import Date


def date_validator(field, value, error):
    try:
        Date.from_string(value)
    except ValueError:
        return error(field, _("{} does not match format '%Y-%m-%d'".format(value)))


S_SET_PERMS_REQUEST_GET = {
    "company_id": {"type": "string", "required": True},
    "user_id": {"type": "string", "required": True},
    "target_company_id": {"type": "string", "required": True},
    "target_user_id": {"type": "string", "required": True},
    "new_role_id": {"type": "string", "required": True},
}

S_SET_PERMS_REQUEST_RETURN = {
    "message": {"type": "boolean", "required": True},
}
