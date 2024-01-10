from unittest import skip

from fastapi import Response, status

from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from ..routers import router as ce_selfconsumption_router


class TestEnergySelfConsumptionAPI(FastAPITransactionCase):
    def test__get_selfconsumption_projects__ok(self) -> None:
        with self._create_test_client(router=ce_selfconsumption_router) as test_client:
            respose: Response = test_client.get("/energy_selfconsumption/projects")

        self.assertEqual(respose.status_code, status.HTTP_200_OK)

    @skip("Skip")
    def test__get_selfconsumption_projects_by_cau__ok(self) -> None:
        with self._create_test_client(router=ce_selfconsumption_router) as test_client:
            respose: Response = test_client.get(
                "/energy_selfconsumption/project/001ES0397277816188340VL"
            )

        self.assertEqual(respose.status_code, status.HTTP_200_OK)
