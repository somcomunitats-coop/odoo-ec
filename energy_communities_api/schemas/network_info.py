from pydantic import BaseModel, ConfigDict, Field

from .base import BaseResponse, PaginationLinks


class NetworkInfo(BaseModel):
    model_config = ConfigDict(title="NetworkInfo")
    """
    General information for an overview of some opendata values for energy community members
    """
    members: int = Field(
        ...,
        title="Members",
        description="Total active members of all energy communities",
    )

    energy_communities_active: int = Field(
        ...,
        title="Active energy communities",
        description="Total active energy communities under energy communities platform",
    )

    energy_communities_goal: int = Field(
        ...,
        title="Energy communities goal",
        description='Number of energy communities to achieve in "suma\'t" campaings',
    )

    energy_communities_total: int = Field(
        ...,
        title="Total energy communities",
        description="Total of open energy communities (active and in activation)",
    )

    inscriptions_in_activation: int = Field(
        ...,
        title="In activation inscriptions",
        description="Total of in activation energy communities inscriptions",
    )


class NetworkInfoResponse(BaseResponse):
    """
    Response for a basic network opendata request
    """

    data: NetworkInfo
    links: PaginationLinks
