from datetime import datetime
from faker import Faker
from mock import patch
from odoo.tests import common
from odoo.exceptions import ValidationError
from .helpers import UserSetupMixin, CompanySetupMixin


faker = Faker(locale='es_ES')

class TestCRMLead(UserSetupMixin, CompanySetupMixin, common.TransactionCase):

    def create_crm_lead(self):
        return self.env["crm.lead"].create({
            "name": "CE Name",
            "email_from": faker.email(),
            "submission_type": "place_submission",
            "company_id": self.coordination.id,
            "source_id": self.env.ref("energy_communities.ce_source_creation_ce_proposal").id,
            "metadata_line_ids": [
                (0, 0, {"key": "current_lang", "value": "en_US"}),
                (0, 0, {"key": "ce_creation_date", "value": "1994-09-01"}),
                (0, 0, {"key": "ce_address", "value": "Av St Narcís"}),
                (0, 0, {"key": "ce_city", "value": "Girona"}),
                (0, 0, {"key": "ce_zip", "value": "17005"}),
                (0, 0, {"key": "contact_phone", "value": "666666666"}),
                (0, 0, {"key": "email_from", "value": "random@somcomunitats.coop"}),
                (0, 0, {"key": "ce_vat", "value": "38948723V"}),
            ]
        })

    def setUp(self):
        super().setUp()

        self.users_model = self.env['res.users']
        self.company_model = self.env['res.company']
        self.role_line_model = self.env["res.users.role.line"]
        self.instance = self.company_model.search([
            ('hierarchy_level', '=', 'instance')
        ])[0]

        self.coordination = self.create_company(
            'Coordinator', 'coordinator', self.instance.id,
        )
        
        self.coord_admin = self.create_user("Coord", "Admin")

        self.make_coord_user(self.coordination, self.coord_admin)

        self.crm_lead = self.create_crm_lead()

    def test__get_default_community_wizard__base_case(self):
        result = self.crm_lead._get_default_community_wizard()

        lang = self.env["res.lang"].search([("code", "=", "en_US")])
        foundation_date = datetime.strptime('1994-09-01', '%Y-%m-%d')
        users = self.crm_lead.company_id.get_users()
        self.assertEquals(result, {
            'name': self.crm_lead.name,
            'city': 'Girona',
            'default_lang_id': lang.id,
            'email': 'random@somcomunitats.coop',
            'foundation_date': foundation_date,
            'hierarchy_level': 'community',
            'parent_id': self.coordination.id,
            'crm_lead_id': self.crm_lead.id,
            'phone': '666666666',
            'street': 'Av St Narcís',
            'vat': '38948723V',
            'zip_code': '17005',
            'user_ids': [user.id for user in users],
            'chart_template_id': self.env["account.chart.template"].search([("name", "=", "PGCE PYMEs 2008")])[0].id,
            'update_default_taxes': True,
            'default_sale_tax_id': self.env["account.tax.template"].search([("name", "=", "IVA 21% (Servicios)")])[0].id,
            'default_purchase_tax_id': self.env["account.tax.template"].search([("name", "=", "21% IVA soportado (bienes corrientes)")])[0].id,
            'property_cooperator_account': self.env.ref("l10n_es.account_common_4400").id,
            'create_user': False,
        })


