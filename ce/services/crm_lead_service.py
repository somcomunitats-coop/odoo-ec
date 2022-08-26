import logging
from odoo.addons.component.core import Component
from . import schemas

_logger = logging.getLogger(__name__)


class CRMLeadService(Component):
    _inherit = "base.rest.private_abstract_service"
    _name = "crm.lead.services"
    _collection = "ce.services"
    _usage = "crm-lead"
    _description = """
        CRMLead requests
    """

    def create(self, **params):
        params = self._prepare_create(params)

        company_id = self._check_company(params['odoo_company_id'])
        params.update({'odoo_company_id': company_id})
        sr = self.env["crm.lead"].sudo().create(params)
        return self._to_dict(sr)

    def _validator_create(self):
        return schemas.S_CRM_LEAD_CREATE

    def _validator_return_create(self):
        return schemas.S_CRM_LEAD_RETURN_CREATE

    @staticmethod
    def _to_dict(crm_lead):
        return {
            "id": crm_lead.id
        }

    def _check_company(self, company_id):
        if company_id == -1:
            coordinator_id = self.env["res.company"].search([('coordinator','=',True)])[0]
            return coordinator_id
        return company_id

    def _prepare_create(self, params):
        return {
            "name": params.get("partner_name"),
            "partner_address_name": params.get("partner_name"),
            "partner_address_email": params.get("partner_email"),
            "partner_address_phone": params.get("partner_phone"),
            "street": params.get("partner_full_address"),
            "city": params.get("partner_city"),
            "zip": params.get("partner_zip"),
            "company_id": params.get("odoo_company_id"),
            "source_id": params.get("source_xml_id"),
            "tag_ids": [(6, 0, params.get("tag_ids", []))],
        }
