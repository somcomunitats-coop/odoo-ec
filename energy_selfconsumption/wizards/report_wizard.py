from odoo import _, api, fields, models


class ReportWizard(models.TransientModel):
    _name = "energy_selfconsumption.report_wizard"
    _description = "Generate Partition Coefficient Report"

    report_data = fields.Text("Report Data", readonly=True)
    file_name = fields.Char("File Name", readonly=True)
    file_data = fields.Binary("File", readonly=True)

    def download_report(self):
        url = "/energy_selfconsumption/download_report?id=%s" % self.id
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }
