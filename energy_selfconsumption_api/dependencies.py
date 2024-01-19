from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from typing_extensions import Annotated

from odoo.api import Environment

from odoo.addons.base.models.res_users import Users
from odoo.addons.fastapi.dependencies import odoo_env

AuthHeader = APIKeyHeader(
    name="api-token",
    description="Api token header",
)


def api_key_authentication(
    api_key: Annotated[str, Depends(AuthHeader)],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Users:
    """
    Search for the user that is associated with api_key
    """
    user_id = env["auth.api.key"].search([("key", "=", api_key)], limit=1).user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )

    return user_id


def authenticated_endpoint(user: Annotated[Users, Depends(api_key_authentication)]):
    pass
