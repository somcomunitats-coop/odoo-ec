import base64
import logging
from io import StringIO

import chardet
import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class DistributionTableImportWizard(models.TransientModel):
    _name = "energy_selfconsumption.distribution_table_import.wizard"
    _description = "Service to import distribution table"

    import_file = fields.Binary(string="Import File (*.csv)")
    fname = fields.Char(string="File Name")
    delimiter = fields.Char(
        default=",",
        required=True,
        string="File Delimiter",
        help="Delimiter in import CSV file.",
    )
    quotechar = fields.Char(
        default='"',
        required=True,
        string="File Quotechar",
        help="Quotechar in import CSV file.",
    )
    encoding = fields.Char(
        default="utf-8",
        required=True,
        string="File Encoding",
        help="Encoding format in import CSV file.",
    )
    clean = fields.Boolean("Clean data", default=True)

    @api.constrains("import_file")
    def _constrains_import_file(self):
        logger.info("\n\n _constrains_import_file")
        if self.fname:
            format = str(self.fname.split(".")[-1])
            if format != "csv":
                raise ValidationError(_("Only csv format files are accepted."))

    def import_file_button(self):
        logger.info("\n\n import_file_button")
        active_id = self.env.context.get("active_id")
        distribution_table = self.env[
            "energy_selfconsumption.distribution_table"
        ].browse(active_id)
        self.parse_csv_file(distribution_table)
        return True

    def parse_csv_file(self, distribution_table):
        logger.info("\n\n parse_csv_file INICIO")
        file_data = base64.b64decode(self.import_file)
        df, not_error = self._parse_file(file_data)
        if not_error and self.check_data_validity(df, distribution_table):
            if self.clean:
                self.clean_lines(distribution_table)
            self.import_all_lines(df, distribution_table)
            if distribution_table.type == "hourly":
                distribution_table.write(
                    {
                        "hourly_coefficients_imported_file": self.import_file,
                        "hourly_coefficients_imported_filename": self.fname,
                        "hourly_coefficients_imported_delimiter": self.delimiter,
                        "hourly_coefficients_imported_quotechar": self.quotechar,
                        "hourly_coefficients_imported_encoding": self.encoding,
                    }
                )
        logger.info("\n\n parse_csv_file FIN")

    def download_template_button(self):
        logger.info("\n\n download_template_button")
        doc_ids = self.env.context.get("active_ids")
        return self.env.ref(
            "energy_selfconsumption.distribution_table_hourly_csv_report"
        ).report_action(docids=doc_ids)

    def _parse_file(self, data_file):
        logger.info("\n\n _parse_file")
        self.ensure_one()
        try:
            try:
                decoded_file = data_file.decode(self.encoding)
            except UnicodeDecodeError:
                detected_encoding = chardet.detect(data_file).get("encoding", False)
                if not detected_encoding:
                    self.notification(
                        "Error", _("No valid encoding was found for the attached file")
                    )
                    return False, False
                decoded_file = data_file.decode(detected_encoding)

            df = pd.read_csv(
                StringIO(decoded_file),
                delimiter=self.delimiter,
                quotechar=self.quotechar,
            )
            return df, True
        except Exception:
            logger.warning("Parser error", exc_info=True)
            self.notification("Error", _("Error parsing the file"))
            return False, False

    def check_data_validity(self, df, distribution_table):
        if distribution_table.type == "hourly":
            grouped = df.groupby(df.columns[0]).sum()
            invalid_hours = grouped[round(grouped.sum(axis=1), 6) != 1.0]
            if not invalid_hours.empty:
                invalid_hours_list = invalid_hours.index.tolist()
                self.env[
                    "energy_selfconsumption.create_distribution_table"
                ].notification(
                    distribution_table,
                    "Error",
                    _(
                        "The sum of coefficients for the following hours is not equal to 1: %s"
                        % ", ".join(map(str, invalid_hours_list))
                    ),
                )
                return False
        elif distribution_table.type == "fixed":
            sum_coefficients = round(df["Coefficient"].sum(), 6)
            if sum_coefficients != 1.0:
                self.env[
                    "energy_selfconsumption.create_distribution_table"
                ].notification(
                    distribution_table,
                    "Error",
                    _(
                        "The sum of coefficients is not equal to 1: %s"
                        % sum_coefficients
                    ),
                )
                return False
        return True

    def clean_lines(self, distribution_table):
        logger.info("\n\n clean_lines")
        distribution_table.supply_point_assignation_ids.unlink()

    def import_all_lines(self, df, distribution_table):
        logger.info("\n\n import_all_lines")
        if distribution_table.type == "fixed":
            values_list = self.prepare_fixed_csv_values(df, distribution_table)
        elif distribution_table.type == "hourly":
            values_list = self.prepare_hourly_csv_values(df, distribution_table)

        self.env[
            "energy_selfconsumption.create_distribution_table"
        ].create_energy_selfconsumption_supply_point_assignation_sql(
            values_list, distribution_table
        )

    def prepare_fixed_csv_values(self, df, distribution_table):
        logger.info("\n\n prepare_fixed_csv_values")
        values_list = []
        for index, row in df.iterrows():
            value = self.get_supply_point_assignation_values(
                row, None, distribution_table
            )
            values_list.append(value)
        return values_list

    def prepare_hourly_csv_values(self, df, distribution_table):
        logger.info("\n\n prepare_hourly_csv_values")
        values_list = []
        for index, row in df.iterrows():
            for column in df.columns[1:]:
                cups = column
                value = self.get_supply_point_assignation_values(
                    row, cups, distribution_table
                )
                values_list.append(value)
            break
        return values_list

    def get_supply_point_assignation_values(self, row, cups, distribution_table):
        if cups:
            supply_point_id = self.get_supply_point_id(cups, distribution_table)
            coefficient = 0
        else:
            supply_point_id = self.get_supply_point_id(row["CUPS"], distribution_table)
            coefficient = row["Coefficient"]

        return {
            "distribution_table_id": self.env.context.get("active_id"),
            "supply_point_id": supply_point_id,
            "coefficient": coefficient,
            "company_id": distribution_table.company_id.id,
        }

    def get_supply_point_id(self, code, distribution_table):
        supply_point_id = self.env["energy_selfconsumption.supply_point"].search_read(
            [("code", "=", code)], ["id"]
        )
        if not supply_point_id:
            self.env["energy_selfconsumption.create_distribution_table"].notification(
                distribution_table,
                "Error",
                _("There isn't any supply point with this code: {code}").format(
                    code=code
                ),
            )
            return "null"
        return supply_point_id[0]["id"]

    def get_coefficient(self, coefficient):
        try:
            return fields.Float.convert_to_write(
                self=fields.Float(),
                value=coefficient,
                record=self.env[
                    "energy_selfconsumption.supply_point_assignation"
                ].coefficient,
            )
        except ValueError:
            return 0
