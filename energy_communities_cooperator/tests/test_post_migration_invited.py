from odoo.upgrade.testing import UpgradeCase


class TestInvitedCooperatorMigration(UpgradeCase):
    def prepare(self):
        old_invited_partners = self.env["res.partner"].search(
            [
                ("company_id", "!=", False),
                ("no_member_autorized_in_energy_actions", "=", True),
            ]
        )
        return old_invited_partners

    def check(self, old_invited_partners):
        invited_cooperators = (
            self.env["cooperative.membership"]
            .sudo()
            .search(
                [
                    ("partner_id", "in", old_invited_partners.id),
                    "|",
                    ("effective_invited", "=", True),
                    ("member", "=", True),
                ]
            )
        )
        self.assertEqual(len(old_invited_partners), len(invited_cooperators))
