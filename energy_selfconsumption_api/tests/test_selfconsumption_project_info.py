from fastapi import Response, status

from odoo.addons.fastapi.tests.common import FastAPITransactionCase


class TestEnergySelfConsumptionAPI(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.default_fastapi_odoo_env = cls.env(
            context=dict(cls.env.context, active_test=False)
        )
        cls.default_fastapi_app = cls.env.ref(
            "energy_selfconsumption_api.api_app"
        )._get_app()
        cls.default_fastapi_running_user = cls.env.ref(
            "energy_communities.res_users_admin_plataforma_demo"
        )

    def test__get_selfconsumption_projects__ok(self) -> None:
        with self._create_test_client() as test_client:
            respose: Response = test_client.get(
                "projects", headers={"api-token": "12345"}
            )

        self.assertEqual(respose.status_code, status.HTTP_200_OK)

    def test__get_selfconsumption_projects_by_cau__ok(self) -> None:
        with self._create_test_client() as test_client:
            respose: Response = test_client.get(
                "projects/001ES0397277816188340VL", headers={"api-token": "12345"}
            )

        self.assertEqual(respose.status_code, status.HTTP_200_OK)
