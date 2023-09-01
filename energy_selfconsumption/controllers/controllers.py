from odoo import http
from odoo.http import request


class ReportController(http.Controller):
    @http.route("/energy_selfconsumption/download_report", type="http", auth="user")
    def download_report(self, **kw):
        wizard = request.env["energy_selfconsumption.report_wizard"].browse(
            int(kw.get("id"))
        )
        content = wizard.report_data
        return request.make_response(
            content,
            [
                ("Content-Type", "application/text"),
                ("Content-Disposition", "attachment; filename=" + wizard.file_name),
            ],
        )
