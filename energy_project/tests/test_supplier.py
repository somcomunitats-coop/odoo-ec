from odoo.tests import common


class TestSupplier(common.SingleTransactionCase):
    def test_supplier_load_xml_id(self):
        fields = ["nif", "order", "name", "phone", "portal"]
        data = [
            [
                "B22215487",
                "R1-285",
                "ENERGIAS DE BENASQUE S.L",
                "900 102 303",
                "https://portal.asemeservicios.com",
            ]
        ]
        load_result = self.env["energy_project.supplier"].load(fields, data)
        supplier_id = self.env["energy_project.supplier"].browse(load_result["ids"])
        xml_id = supplier_id.get_external_id()
        self.assertEqual(xml_id[supplier_id.id], "energy_project.supplier_R1-285")
