from odoo import api, fields, models

INSCRIPTION_IMPORT_TEMPLATE_PARAM = (
    "energy_selfconsumption.inscription_import_template_attachment_id"
)
DEFAULT_INSCRIPTION_IMPORT_TEMPLATE_XMLID = (
    "energy_selfconsumption.selfconsumption_table_example_attachment"
)


class ResConfigSettings(models.TransientModel):
    """Inscription import template on the standard Energy Project settings."""

    _inherit = "res.config.settings"

    inscription_import_template = fields.Binary(
        string="Inscription import template",
        help="File downloaded from the inscription import wizard.",
    )
    inscription_import_template_filename = fields.Char(
        string="Inscription import template filename",
    )

    @api.model
    def _inscription_import_template_attachment(self):
        """Return the uploaded template, or the file shipped with the module."""
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(INSCRIPTION_IMPORT_TEMPLATE_PARAM)
        )
        if param:
            attachment = self.env["ir.attachment"].sudo().browse(int(param)).exists()
            if attachment:
                return attachment
        return self.env.ref(
            DEFAULT_INSCRIPTION_IMPORT_TEMPLATE_XMLID, raise_if_not_found=False
        )

    @api.model
    def get_values(self):
        """Show the current import template in the settings form."""
        res = super().get_values()
        attachment = self._inscription_import_template_attachment()
        if attachment:
            res.update(
                {
                    "inscription_import_template": attachment.datas,
                    "inscription_import_template_filename": attachment.name,
                }
            )
        return res

    def set_values(self):
        """Store an uploaded template without overwriting the module data file."""
        super().set_values()
        for settings in self:
            if settings.inscription_import_template:
                settings._save_inscription_import_template()

    def _save_inscription_import_template(self):
        """Keep the uploaded file in its own attachment."""
        self.ensure_one()
        Attachment = self.env["ir.attachment"].sudo()
        parameter = self.env["ir.config_parameter"].sudo()
        current = self._inscription_import_template_attachment()
        default = self.env.ref(
            DEFAULT_INSCRIPTION_IMPORT_TEMPLATE_XMLID, raise_if_not_found=False
        )
        filename = self.inscription_import_template_filename or (
            current.name if current else "inscription_import_template.csv"
        )
        values = {
            "name": filename,
            "datas": self.inscription_import_template,
            "public": True,
            "company_id": False,
        }
        if not current or (default and current == default):
            current = Attachment.create(values)
        else:
            current.write(values)
        parameter.set_param(INSCRIPTION_IMPORT_TEMPLATE_PARAM, str(current.id))
