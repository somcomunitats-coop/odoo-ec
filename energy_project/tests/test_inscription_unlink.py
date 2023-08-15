from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import logging

log = logging.getLogger(__name__)


class TestInscriptionUnlink(TransactionCase):
    tags = ['energy_project']

    def setUp(self):
        super(TestInscriptionUnlink, self).setUp()

        self.company = self.env['res.company'].create({'name': 'Company'})
        self.project = self.env['energy_project.project'].create({'name': 'Project'})
        self.partner = self.env['res.partner'].create({'name': 'Partner'})
        self.inscription = self.env['energy_project.inscription'].create({
            'company_id': self.company.id,
            'project_id': self.project.id,
            'partner_id': self.partner.id,
            'effective_date': '2023-08-15',
        })

    def test_unlink_no_matching_assignations(self):
        log.info('Test 1: No matching assignations')
        self.inscription.unlink()
        self.assertFalse(self.inscription.exists())

    def test_unlink_with_matching_assignations(self):
        log.info('Test 2: Matching assignations for the inscription')
        assignation = self.env['energy_selfconsumption.supply_point_assignation'].create({
            'distribution_table_id': self.project.selfconsumption_id.distribution_tables_ids[0].id,
            'selfconsumption_project_id': self.project.id,
            'supply_point_id': self.partner.id,
        })

        with self.assertRaises(ValidationError):
            self.inscription.unlink()

    def test_unlink_with_matching_assignations_to_remove(self):
        log.info('Test 3: Matching assignations for removal')
        assignation = self.env['energy_selfconsumption.supply_point_assignation'].create({
            'distribution_table_id': self.project.selfconsumption_id.distribution_tables_ids[0].id,
            'selfconsumption_project_id': self.project.id,
            'supply_point_id': self.partner.id,
        })

        self.inscription.unlink()
        self.assertFalse(self.inscription.exists())
        self.assertFalse(assignation.exists())
