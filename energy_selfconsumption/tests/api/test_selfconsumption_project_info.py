from fastapi import Response, status

from odoo.addons.fastapi.routers import demo_router
from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from ...api.selfconsumption_project_info import EnergySelfConsumptionAPI


class TestEnergySelfConsumptionAPI(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.default_fastapi_running_user = cls.env.ref(
            EnergySelfConsumptionAPI.API_NAME
        )
        # cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create(
        #     {"name": "CoordinadoraCE"}
        # )

    def test__get_selfconsumption_projects__ok(self) -> None:
        with self._create_test_client(router=demo_router) as test_client:
            respose: Response = test_client.get("/self-consumption")

        self.assertEqual(respose.status_code, status.HTTP_200_OK)
