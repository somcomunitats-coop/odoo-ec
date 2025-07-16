from datetime import datetime

from odoo.addons.energy_communities.utils import product_utils

from ..schemas import (
    PackProductCreationData,
    ProductCreationParams,
    ServiceProductCreationData,
    ServiceProductExistingData,
)
from .testing_cases import (
    PackProductDataTestingCase,
    ServiceProductCreationDataTestingCase,
    ServiceProductExistingDataTestingCase,
)


class ServiceInvoicingTestingProductCreator:
    _name = (
        "energy_communities_service_invoicing.service_invoicing_testing_product_creator"
    )

    def _prepare_all_case_data(self, case):
        new_services = []
        existing_services = []
        for service_data in case.service_product_case:
            if isinstance(service_data, ServiceProductCreationDataTestingCase):
                new_services.append(
                    self._prepare_one_case_data(
                        service_data,
                        ServiceProductCreationDataTestingCase,
                        ServiceProductCreationData,
                    )
                )
            if isinstance(service_data, ServiceProductExistingDataTestingCase):
                existing_services.append(
                    self._prepare_one_case_data(
                        service_data,
                        ServiceProductExistingDataTestingCase,
                        ServiceProductExistingData,
                    )
                )
        return ProductCreationParams(
            pack=self._prepare_one_case_data(
                case.pack_product_case,
                PackProductDataTestingCase,
                PackProductCreationData,
            ),
            new_services=new_services,
            existing_services=existing_services,
        )

    def _prepare_one_case_data(
        self, product_case, testing_case_class, product_creation_data_class
    ):
        if product_case:
            params = {}
            for field in testing_case_class._fields:
                data_val = getattr(product_case, field)
                if data_val:
                    if field == "company_id":
                        params[field] = (
                            self.env["res.company"]
                            .search([("name", "=", data_val)], limit=1)
                            .id
                            if data_val
                            else None
                        )
                    elif field in ["categ_id", "product_template_id", "qty_formula_id"]:
                        params[field] = self.env.ref(data_val).id
                    elif field == "taxes_id":
                        params[field] = self._prepare_refs_data(data_val)
                    else:
                        if data_val:
                            params[field] = data_val
            return product_creation_data_class(**params)
        return False

    def _prepare_refs_data(self, refs):
        vals = []
        for ref in refs:
            vals.append((4, self.env.ref(ref).id))
        return vals

    def _assign_pack_to_partner(self, pack, partner):
        payment_mode = self.env["account.payment.mode"].search(
            [("company_id", "=", pack.company_id.id)], limit=1
        )
        aptp_wizard = self.env["assign.pack.to.partner.wizard"].create(
            {
                "activation_date": datetime.now(),
                "pack_id": pack.id,
                "payment_mode_id": payment_mode.id,
                "partner_mids": [(4, partner.id)],
            }
        )
        aptp_wizard.execute_assignation()
        return self.env["contract.contract"].search(
            [("partner_id", "=", partner.id)], limit=1
        )

    def _create_pack_product(self, case):
        data = self._prepare_all_case_data(case)
        with product_utils(self.env) as component:
            result = component.create_products(data)
        return result.pack_product_template
