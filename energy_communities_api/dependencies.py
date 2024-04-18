from fastapi import Depends, HTTPException, Query, status
from fastapi.security import APIKeyHeader
from typing_extensions import Annotated

from odoo.api import Environment

from odoo.addons.base.models.res_users import Users
from odoo.addons.fastapi.dependencies import odoo_env

from .schemas import PaginationLimits
from .services import EnergySelfconsumptionService

DEFAULT_PAGE_SIZE = 20

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
    return user


def paging(
    page: Annotated[int, Query(gte=1)] = 1,
    page_size: Annotated[int, Query(gte=1)] = DEFAULT_PAGE_SIZE,
) -> PaginationLimits:
    return PaginationLimits(
        limit=page_size,
        offset=(page - 1) * page_size,
        page=page,
    )


def energy_selfconsumption_service(
    env: Annotated[Environment, Depends(odoo_env)],
    auth_user: Annotated[Users, Depends(authenticated_endpoint)],
) -> EnergySelfconsumptionService:
    return EnergySelfconsumptionService(env=env, user=auth_user)


PagingDependency = Annotated[PaginationLimits, Depends(paging)]
EnergySelfconsumptionDependency = Annotated[
    EnergySelfconsumptionService, Depends(energy_selfconsumption_service)
]
