from odoo import api, fields, models


class MailTemplate(models.Model):
    _name = "mail.template"
    _inherit = ["mail.template", "user.currentcompany.mixin"]

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
                    and "[%s] "
                    % (
                        template.company_id.comercial_name
                        if template.company_id.comercial_name
                        else template.company_id.name
                    )
                    or "[GLOBAL] ",
                    template.name,
                ),
            )
            for template in self
        ]

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {}, company_id=self.env.company.id)
        return super().copy(default=default)
