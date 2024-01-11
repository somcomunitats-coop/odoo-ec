import sys

if sys.version_info >= (3, 9):
    from typing import Any, List
else:
    from typing_extensions import Any, Annotated, List

from odoo.api import Environment

from ..schemas import SelfConsumptionProjectInfo


def get_selfconsumption_projects(
    env: Environment,
    cau: Any,
) -> List[SelfConsumptionProjectInfo]:
    search_domain = bool(cau) and [("code", "=", cau)] or []
    return [
        SelfConsumptionProjectInfo(
            cau=project.code,
            project_name=project.name,
            ce_id=project.project_id.id,
            ce_name=project.company_id.name,
            power=project.power,
        )
        for project in env["energy_selfconsumption.selfconsumption"].search(
            search_domain
        )
    ]
