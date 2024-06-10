import csv
import random
from io import StringIO

from odoo import models


class DistributionTableCSV(models.AbstractModel):
    _name = "report.energy_selfconsumption.distribution_table.csv"
    _inherit = "report.report_csv.abstract"

    def create_csv_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)

        distribution_table = objs[0]
        list_cups = (
            distribution_table.selfconsumption_project_id.inscription_ids.mapped(
                "partner_id.supply_ids.code"
            )
        )

        file_data = StringIO()
        file = csv.DictWriter(file_data, **self.csv_report_options(list_cups, distribution_table.type))
        self.generate_csv_report(file, data, list_cups, distribution_table)
        file_data.seek(0)
        return file_data.read(), "csv"

    def generate_csv_report(self, writer, data, list_cups, distribution_table):
        writer.writeheader()

        def normalize_and_adjust(cups):
            sum_coefficients = sum(cups.values())
            for key in cups:
                cups[key] = cups[key] / sum_coefficients
            # Redondear a 6 decimales y ajustar el último coeficiente
            rounded_cups = {key: round(cups[key], 6) for key in cups}
            sum_rounded = sum(rounded_cups.values())
            last_key = list(rounded_cups.keys())[-1]
            # Ajustar el último coeficiente
            rounded_cups[last_key] += round(1 - round(sum_rounded, 6), 6)
            return rounded_cups

        def format_number(number):
            return "{:.6f}".format(number)

        if distribution_table.type == "fixed":
            cups = {code: random.random() for code in list_cups}
            cups = normalize_and_adjust(cups)

            # Writing the rows
            for key, value in cups.items():
                writer.writerow({'CUPS': key, 'Coefficient': format_number(value)})
        else:
            for hour in range(1, 8751):
                cups = {code: random.random() for code in list_cups}
                cups = normalize_and_adjust(cups)

                row = {"hour": hour}
                row.update({k: format_number(v) for k, v in cups.items()})
                writer.writerow(row)

    def csv_report_options(self, list_cups, report_type):
        res = super().csv_report_options()
        if report_type == "fixed":
            res["fieldnames"] = ["CUPS", "Coefficient"]
        else:
            res["fieldnames"] = ["hour"]
            res["fieldnames"].extend(list_cups)
        res["delimiter"] = ","
        res["quotechar"] = '"'
        return res
