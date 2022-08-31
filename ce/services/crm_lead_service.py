import logging
from odoo.addons.component.core import Component
from odoo.addons.base_rest.http import wrapJsonException
from werkzeug.exceptions import BadRequest
from odoo import _
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
        company_id = self.env['res.company'].get_real_ce_company_id(params['odoo_company_id']).id
        params.update({'odoo_company_id': company_id})

        sources = {s.name:s.res_id for s in self.env['ir.model.data'].search([
            ('module','=','ce'), ('model','=','utm.source')])}
        if params['source_xml_id'] not in sources:
            raise wrapJsonException(
                BadRequest(
                    _("Source {} not found").format(
                        params["source_xml_id"])
                ),
                include_description=True,
            )

        params.update({'source_xml_id': sources[params['source_xml_id']]})

        for tag_id in params['tag_ids']:
            tag_id_res = self.env['crm.lead.tag'].search([('id','=',tag_id)]).id
            if not tag_id_res:
                raise wrapJsonException(
                    BadRequest(
                        _("Tag {} not found").format(tag_id)
                    ),
                    include_description=True,
                )

        params = self._prepare_create(params)
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
