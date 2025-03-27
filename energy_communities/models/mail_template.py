from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    company_id = fields.Many2one(required=False, default=lambda self: self.env.company)

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(["name", "company_id"])
        return [
            (
                template.id,
                "%s%s"
                % (
                    template.company_id
                    and "[%s] " % template.company_id.name
                    or "[GLOBAL] ",
                    template.name,
                ),
            )
            for template in self
        ]
