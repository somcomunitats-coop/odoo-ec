import csv
import random
from io import StringIO

from odoo import models


class DistributionTableCSV(models.AbstractModel):
    _name = "report.energy_selfconsumption.distribution_table.csv"
    _inherit = "report.report_csv.abstract"

    def create_csv_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)

        distribution_table_id = objs[0]
        list_cups = (
            distribution_table_id.selfconsumption_project_id.inscription_ids.mapped(
                "partner_id.supply_ids.code"
            )
        )

        file_data = StringIO()
        file = csv.DictWriter(file_data, **self.csv_report_options(list_cups))
        self.generate_csv_report(file, data, list_cups)
        file_data.seek(0)
        return file_data.read(), "csv"

    def generate_csv_report(self, writer, data, list_cups):
        writer.writeheader()

        for hour in range(1, 8751):
            cups = {}
            cups.update({code: random.random() for code in list_cups})
            coefficients = cups.values()
            sum_coefficients = sum(coefficients)
            for key, value in cups.items():
                cups[key] = value / sum_coefficients
            # Add the normalized coefficients to the row
            row = {"hour": hour}
            row.update(cups)
            writer.writerow(row)

    def csv_report_options(self, list_cups):
        res = super().csv_report_options()
        res["fieldnames"].append("hour")
        res["fieldnames"].extend(list_cups)
        res["delimiter"] = ","
        res["quotechar"] = '"'
        return res
