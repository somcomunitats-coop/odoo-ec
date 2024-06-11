import base64
import logging
from datetime import datetime
from io import StringIO

import chardet
import pandas as pd

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger(__name__)


class DistributionTableImportWizard(models.TransientModel):
    _name = "energy_selfconsumption.distribution_table_import.wizard"

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
        if not_error and self.check_data_validity(df, distribution_table.type):
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

    def check_data_validity(self, df, table_type):
        if table_type == "hourly":
            grouped = df.groupby(df.columns[0]).sum()
            invalid_hours = grouped[round(grouped.sum(axis=1), 6) != 1.0]
            if not invalid_hours.empty:
                invalid_hours_list = invalid_hours.index.tolist()
                self.notification(
                    "Error",
                    _(
                        "The sum of coefficients for the following hours is not equal to 1: %s"
                        % ", ".join(map(str, invalid_hours_list))
                    ),
                )
                return False
        elif table_type == "fixed":
            sum_coefficients = round(df["Coefficient"].sum(), 6)
            if sum_coefficients != 1.0:
                self.notification(
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
        self.bulk_insert_sql(values_list)

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

    def bulk_insert_sql(self, values_list):
        if not values_list:
            return

        error = False

        columns = [
            "distribution_table_id",
            "supply_point_id",
            "coefficient",
            "company_id",
            "create_uid",
            "create_date",
            "write_uid",
            "write_date",
        ]
        data = [
            (
                self.env.context.get("active_id"),
                value["supply_point_id"],
                float(value["coefficient"]),
                value["company_id"],
                self.env.user.id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.env.user.id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            for value in values_list
        ]
        query = f"""INSERT INTO energy_selfconsumption_supply_point_assignation
        ({', '.join(columns)})
        VALUES {', '.join(['%s'] * len(data))}"""
        logger.error(f"\n\n SQL: \n {query}")
        try:
            self.env.cr.execute(query, data)
            self.env.cr.commit()
        except Exception as e:
            self.env.cr.rollback()
            error = True
            logger.error(f"Error executing bulk insert query: {e}")
            self.notification("Error query", f"Query: {query}\nError: {e}")

        if not error:
            self.notification("Import", "Import completed successfully")

    def get_supply_point_assignation_values(self, row, cups, distribution_table):
        if cups:
            supply_point_id = self.get_supply_point_id(code=cups)
            coefficient = 0
        else:
            supply_point_id = self.get_supply_point_id(code=row["CUPS"])
            coefficient = row["Coefficient"]

        return {
            "distribution_table_id": self.env.context.get("active_id"),
            "supply_point_id": supply_point_id,
            "coefficient": coefficient,
            "company_id": distribution_table.company_id.id,
        }

    def get_supply_point_id(self, code):
        supply_point_id = self.env["energy_selfconsumption.supply_point"].search_read(
            [("code", "=", code)], ["id"]
        )
        if not supply_point_id:
            self.notification(
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

    def notification(self, subject, body):
        active_id = self.env.context.get("active_id")
        distribution_table = self.env[
            "energy_selfconsumption.distribution_table"
        ].browse(active_id)
        try:
            distribution_table.message_post(
                body=body,
                subject=subject,
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
