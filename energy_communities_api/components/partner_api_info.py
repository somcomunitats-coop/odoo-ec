import base64
from datetime import date
from typing import List

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.component.core import Component

from ..schemas import (
    CommunityInfo,
    CommunityServiceInfo,
    CommunityServiceMetricsInfo,
    InvoiceInfo,
    InvoicePDFInfo,
    MemberInfo,
)


class PartnerApiInfo(Component):
    _name = "partner.api.info"
    _inherit = "api.info"
    _usage = "api.info"
    _apply_on = "res.partner"

    _communities_domain = lambda _, partner: [
        "&",
        ("partner_id", "=", partner.id),
        "|",
        ("member", "=", True),
        ("old_member", "=", True),
    ]

    _active_communities_services_domain = lambda _, partner: [
        ("partner_id", "=", partner.id),
        ("project_id.state", "=", "active"),
    ]

    _active_community_services_domain = lambda _, service_id: [
        ("id", "=", service_id),
        ("state", "=", "active"),
    ]

    _member_invoices = lambda _, partner: [
        ("partner_id", "=", partner.id),
        ("state", "=", "posted"),
        ("journal_id.type", "=", "sale"),
    ]

    def get_member_info(self, partner: Partner) -> MemberInfo:
        return self.get(partner)

    def total_member_communities(self, partner: Partner) -> int:
        domain = self._communities_domain(partner)
        return self.env["cooperative.membership"].search_count(domain)

    def get_member_communities(self, partner: Partner) -> CommunityInfo:
        communities = self._get_communities(partner)
        if communities:
            return self.get_list(communities)
        return []

    def total_member_active_community_services(self, partner: Partner) -> int:
        domain = self._active_communities_services_domain(partner)
        return self.env["energy_project.inscription"].search_count(domain)

    def get_member_community_services(
        self, partner: Partner
    ) -> List[CommunityServiceInfo]:
        community_services = []
        domain = self._active_communities_services_domain(partner)
        active_community_services = self.env["energy_project.inscription"].search(
            domain
        )
        for service in active_community_services:
            member_contract = service.project_id.get_member_contract(partner)
            if member_contract:
                service_info = CommunityServiceInfo(
                    id=service.project_id.id,
                    type="fotovoltaic",
                    name=service.project_id.name,
                    status=service.project_id.state,
                    has_monitoring=service.project_id.monitoring_service() is not None,
                    shares=member_contract.supply_point_assignation_id.coefficient,
                    inscription_date=member_contract.date_start.strftime("%Y-%m-%d"),
                    inscriptions=len(service.project_id.inscription_ids),
                )
                community_services += [service_info]
        return community_services

    def get_member_community_service_detail(
        self, partner: Partner, service_id: int
    ) -> CommunityServiceInfo:
        domain = self._active_community_services_domain(service_id)
        project = self.env["energy_project.project"].search(domain)
        if not project:
            return None

        member_contract = project.get_member_contract(partner)
        if not member_contract:
            return None

        return CommunityServiceInfo(
            id=project.id,
            type="fotovoltaic",
            name=project.name,
            status=project.state,
            has_monitoring=project.monitoring_service() is not None,
            shares=member_contract.supply_point_assignation_id.coefficient,
            inscription_date=member_contract.date_start.strftime("%Y-%m-%d"),
            inscriptions=len(project.inscription_ids),
        )

    def get_member_community_services_metrics(
        self, partner: Partner, date_from: date, date_to: date
    ) -> List[CommunityServiceMetricsInfo]:
        metrics = []
        domain = self._active_communities_services_domain(partner)
        projects = (
            self.env["energy_project.inscription"]
            .search(domain)
            .mapped(lambda inscription: inscription.project_id)
        )
        for project in projects:
            metrics_component = self.component(usage="metrics.info")
            metrics_info = metrics_component.get_project_metrics_by_member(
                project, partner, date_from, date_to
            )
            if metrics_info:
                metrics += [metrics_info]
        return metrics

    def get_member_community_services_metrics_by_service(
        self, partner: Partner, service_id: int, date_from: date, date_to: date
    ) -> CommunityServiceMetricsInfo:
        domain = self._active_community_services_domain(service_id)
        project = self.env["energy_project.project"].search(domain)
        if project:
            metrics_component = self.component(usage="metrics.info")
            metrics_info = metrics_component.get_project_metrics_by_member(
                project, partner, date_from, date_to
            )
            return metrics_info

    def get_total_member_invoices(self, partner: Partner) -> int:
        return len(self._get_invoices(partner))

    def get_member_invoices(self, partner: Partner) -> List[InvoiceInfo]:
        invoices = self._get_invoices(partner)
        return [
            InvoiceInfo(
                id=invoice.id,
                number=invoice.display_name,
                service_type=invoice.service_type,
                state=invoice.payment_state_for_api,
                amount_total=invoice.amount_total,
                date=str(invoice.date),
                pdf_url="{base_url}/me/invoices/{id}/download".format(
                    base_url=self.env.company.get_base_url(), id=invoice.id
                ),
            )
            for invoice in invoices
        ]

    def get_member_invoice_by_id(
        self, partner: Partner, invoice_id: int
    ) -> InvoiceInfo:
        invoices = self._get_invoices(partner, invoice_id)
        if not invoices:
            return None
        invoice = invoices[0]
        return InvoiceInfo(
            id=invoice.id,
            number=invoice.display_name,
            service_type=invoice.service_type,
            state=invoice.payment_state_for_api,
            amount_total=invoice.amount_total,
            date=str(invoice.date),
            pdf_url="{base_url}/me/invoices/{id}/download".format(
                base_url=self.env.company.get_base_url(), id=invoice.id
            ),
        )

    def get_member_invoice_pdf_by_id(
        self, partner: Partner, invoice_id: int
    ) -> InvoiceInfo:
        invoices = self._get_invoices(partner, invoice_id)
        if not invoices:
            return None
        invoice = invoices[0]
        report = self.env["ir.actions.report"]._get_report_from_name(
            "account.report_invoice_with_payments"
        )
        pdf_content, _ = self.env["ir.actions.report"]._render_qweb_pdf(
            report.report_name, invoice.id
        )
        return InvoicePDFInfo(id=invoice.id, content=base64.b64encode(pdf_content))

    def _get_communities(self, partner: Partner):
        domain = self._communities_domain(partner)
        if self.work.paging:
            return (
                self.env["cooperative.membership"]
                .search(
                    domain, limit=self.work.paging.limit, offset=self.work.paging.offset
                )
                .mapped(lambda record: record.company_id)
            )
        return (
            self.env["cooperative.membership"]
            .search(domain)
            .mapped(lambda record: record.company_id)
        )

    def _get_invoices(self, partner: Partner, invoice_id: int = None):
        domain = self._member_invoices(partner)
        if invoice_id:
            domain += [("id", "=", invoice_id)]
        return (
            self.env["account.move"]
            .search(domain)
            .filtered(lambda record: record.company_id == partner.company_id)
        )
