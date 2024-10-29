from odoo import api, fields, models


class MassMailingList(models.Model):
    _name = "mailing.list"
    _inherit = ["mailing.list", "user.currentcompany.mixin"]

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    sync_domain = fields.Char(
        string="Synchronization critera",
        default="[('is_blacklisted', '=', False),('email', '!=', False),('company_ids', '!=', False)]",
        required=True,
        help="Filter partners to sync in this list",
    )

    # Compute number of contacts non opt-out, non blacklisted and valid email recipient for a mailing list
    # Overwriten adding company_id control. Please check core module to maintain this method up to date
    def _compute_contact_nbr(self):
        if self.ids:
            self.env.cr.execute(
                """
                select
                    list_id, count(*)
                from
                    mailing_contact_list_rel r
                    left join mailing_contact c on (r.contact_id=c.id and c.company_id=%(current_company_id)s)
                    left join mail_blacklist bl on c.email_normalized = bl.email and bl.active
                where
                    list_id in %(list_ids)s
                    AND COALESCE(r.opt_out,FALSE) = FALSE
                    AND c.email_normalized IS NOT NULL
                    AND bl.id IS NULL
                group by
                    list_id
            """,
                {
                    "list_ids": tuple(self.ids),
                    "current_company_id": self.env.company.id,
                },
            )
            data = dict(self.env.cr.fetchall())
            for mailing_list in self:
                mailing_list.contact_nbr = data.get(mailing_list._origin.id, 0)
        else:
            self.contact_nbr = 0
