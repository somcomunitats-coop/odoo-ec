import csv
from io import StringIO

from odoo import models


class DistributionTableCSV(models.AbstractModel):
    _name = "report.contract_contract.csv"
    _description = "Report contract"
    _inherit = "report.report_csv.abstract"

    def create_csv_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)

        contracts = objs

        file_data = StringIO()
        file = csv.DictWriter(file_data, **self.csv_report_options())
        self.generate_csv_report(file, data, contracts)
        file_data.seek(0)
        return file_data.read(), "csv"

    def generate_csv_report(self, writer, data, contracts):
        writer.writeheader()

        # Writing the rows
        for contract in contracts:
            main_line = contract.get_main_line()
            next_period_date_start = (
                main_line.next_period_date_start
                if main_line
                else contract.contract_line_ids[0].next_period_date_start
            )
            next_period_date_end = (
                main_line.next_period_date_end
                if main_line
                else contract.contract_line_ids[0].next_period_date_end
            )
            writer.writerow(
                {
                    "CUPS": contract.supply_point_assignation_id.supply_point_id.code,
                    "Energia a facturar (kWh)": "0,02",
                    "CAU": contract.project_id.selfconsumption_id.code,
                    "Periode facturat start (dd/mm/aaaa)": next_period_date_start.strftime(
                        "%d/%m/%Y"
                    ),
                    "Periode facturat end (dd/mm/aaaa)": next_period_date_end.strftime(
                        "%d/%m/%Y"
                    ),
                }
            )

    def csv_report_options(self):
        res = super().csv_report_options()
        res["fieldnames"] = [
            "CUPS",
            "Energia a facturar (kWh)",
            "CAU",
            "Periode facturat start (dd/mm/aaaa)",
            "Periode facturat end (dd/mm/aaaa)",
        ]
        res["delimiter"] = ","
        res["quotechar"] = '"'
        return res
