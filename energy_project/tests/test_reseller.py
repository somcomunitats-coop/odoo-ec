from odoo.exceptions import ValidationError
from odoo.tests import common


class TestReseller(common.SingleTransactionCase):
    def test_reseller_load_xml_id(self):
        fields = [
            "order",
            "name",
            "address",
            "zip",
            "city",
            "province",
            "phone",
            "scope",
            "vat",
            "inscription_date",
            "uninscription_date",
            "web",
            "state",
        ]
        data = [
            [
                "R2-9999",
                "ENDESA ENERGÍA S.A.U.",
                "C/ RIBERA DEL LOIRA, Nº 60",
                "28042",
                "MADRID",
                "Madrid",
                "800 760 909",
                "N; INTER AND",
                "A81948077",
                "2023-01-01",
                "2023-02-02",
                "www.endesaclientes.com",
                "Baja",
            ]
        ]
        load_result = self.env["energy_project.reseller"].load(fields, data)
        reseller_id = self.env["energy_project.reseller"].browse(load_result["ids"])
        xml_id = reseller_id.get_external_id()
        self.assertEqual(xml_id[reseller_id.id], "energy_project.reseller_R2-9999")
