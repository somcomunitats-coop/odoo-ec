from odoo import http
from odoo.http import request


class ReportController(http.Controller):
    @http.route("/energy_selfconsumption/download_report", type="http", auth="user")
    def download_report(self, **kw):
        coefficient_report = request.env[
            "energy_selfconsumption.coefficient_report"
        ].browse(int(kw.get("id")))
        content = coefficient_report.report_data
        return request.make_response(
            content,
            [
                ("Content-Type", "application/text; charset=utf-8"),
                (
                    "Content-Disposition",
                    "attachment; filename=" + coefficient_report.file_name,
                ),
            ],
        )
