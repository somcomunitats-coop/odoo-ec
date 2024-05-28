import base64
import logging
from datetime import datetime

import chardet
import pandas as pd
from io import StringIO
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
            "energy_selfconsumption.distribution_table"].browse(active_id)
        self.parse_csv_file(distribution_table)
        return True

    def parse_csv_file(self, distribution_table):
        logger.info("\n\n parse_csv_file INICIO")
        file_data = base64.b64decode(self.import_file)
        df = self._parse_file(file_data)
        self.check_data_validity(df, distribution_table.type)
        self.import_all_lines(df, distribution_table)
        logger.info("\n\n parse_csv_file FIN")

    def download_template_button(self):
        logger.info("\n\n download_template_button")
        active_id = self.env.context.get("active_id")
        distribution_table = self.env[
            "energy_selfconsumption.distribution_table"].browse(active_id)

        if distribution_table.type == "fixed":
            distribution_table_example_attachment = self.env.ref(
                "energy_selfconsumption.distribution_table_example_attachment")
            download_url = "/web/content/{}/?download=true".format(
                str(distribution_table_example_attachment.id))
            return {
                "type": "ir.actions.act_url",
                "url": download_url,
                "target": "new",
            }
        elif distribution_table.type == "hourly":
            doc_ids = self.env.context.get("active_ids")
            return self.env.ref(
                "energy_selfconsumption.distribution_table_hourly_csv_report").report_action(
                docids=doc_ids)

    def _parse_file(self, data_file):
        logger.info("\n\n _parse_file")
        self.ensure_one()
        try:
            try:
                decoded_file = data_file.decode(self.encoding)
            except UnicodeDecodeError:
                detected_encoding = chardet.detect(data_file).get("encoding", False)
                if not detected_encoding:
                    raise UserError(
                        _("No valid encoding was found for the attached file"))
                decoded_file = data_file.decode(detected_encoding)

            df = pd.read_csv(StringIO(decoded_file), delimiter=self.delimiter,
                             quotechar=self.quotechar)
            return df
        except Exception:
            logger.warning("Parser error", exc_info=True)
            raise UserError(_("Error parsing the file"))

    def check_data_validity(self, df, table_type):
        logger.info("\n\n check_data_validity")
        if table_type == "hourly":
            grouped = df.groupby(df.columns[0]).sum()
            invalid_hours = grouped[round(grouped.sum(axis=1), 5) != 1]
            if not invalid_hours.empty:
                invalid_hours_list = invalid_hours.index.tolist()
                raise ValidationError(
                    _("The sum of coefficients for the following hours is not equal to 1: %s" % ", ".join(
                        map(str, invalid_hours_list))))

    def import_all_lines(self, df, distribution_table):
        logger.info("\n\n import_all_lines")
        type = distribution_table.type
        if type == "fixed":
            values_list = self.prepare_fixed_csv_values(df, distribution_table)
        elif type == "hourly":
            values_list = self.prepare_hourly_csv_values(df, distribution_table)

        # Insert all records in bulk
        # self.bulk_insert(values_list)
        self.bulk_insert_sql(values_list)

    def prepare_fixed_csv_values(self, df, distribution_table):
        logger.info("\n\n prepare_fixed_csv_values")
        values_list = []
        for index, row in df.iterrows():
            if index == 0:
                continue  # Skip header row
            value = self.get_supply_point_assignation_values(row, distribution_table)
            values_list.append(value)
        return values_list

    def prepare_hourly_csv_values(self, df, distribution_table):
        logger.info("\n\n prepare_hourly_csv_values")
        values_list = []
        for index, row in df.iterrows():
            if index == 0:
                continue  # Skip header row
            hour = row[0]
            for column in df.columns[1:]:
                cups = column
                value = self.get_supply_point_hourly_assignation_values(
                    row[column], hour, cups, distribution_table
                )
                values_list.append(value)
        return values_list

    def bulk_insert(self, values_list):
        logger.info("\n\n bulk_insert")
        if values_list:
            self.env["energy_selfconsumption.supply_point_assignation"].sudo().create(
                values_list)

    def bulk_insert_sql(self, values_list):
        if not values_list:
            return

        columns = ["distribution_table_id", "supply_point_id", "coefficient", "company_id", "hour", "create_uid", "create_date", "write_uid", "write_date"]
        data = [
            (
                self.env.context.get("active_id"),
                value["supply_point_id"],
                value["coefficient"],
                value["company_id"],
                value.get("hour"),
                1,
                datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
                1,
                datetime.now().strftime("%m/%d/%Y %H:%M:%S"),
            )
            for value in values_list
        ]
        query = f"""INSERT INTO energy_selfconsumption_supply_point_assignation 
        ({', '.join(columns)}) 
        VALUES {str(data).replace('[','').replace(']','')};"""
        try:
            self.env.cr.execute(query)
            self.env.cr.commit()
        except Exception as e:
            raise ValidationError("\n\n Error query :"+str(e))

        query = f""" INSERT INTO energy_selfconsumption_supply_point_group_rel 
        (energy_selfconsumption_distribution_table_id,
        energy_selfconsumption_supply_point_id) 
        select distribution_table_id,supply_point_id 
        from energy_selfconsumption_supply_point_assignation 
        group by distribution_table_id,supply_point_id 
        having distribution_table_id={self.env.context.get("active_id")}"""

        try:
            self.env.cr.execute(query)
            self.env.cr.commit()
        except Exception as e:
            raise ValidationError("\n\n Error query :"+str(e))

    def get_supply_point_assignation_values(self, row, distribution_table):
        return {
            "distribution_table_id": self.env.context.get("active_id"),
            "supply_point_id": self.get_supply_point_id(code=row[0]),
            "coefficient": self.get_coefficient(coefficient=row[1]),
            "company_id": distribution_table.company_id.id,
        }

    def get_supply_point_hourly_assignation_values(self, coefficient, hour, cups,
                                                   distribution_table):
        return {
            "distribution_table_id": self.env.context.get("active_id"),
            "hour": self.get_hour(hour=hour),
            "supply_point_id": self.get_supply_point_id(code=cups),
            "coefficient": self.get_coefficient(coefficient=coefficient),
            "company_id": distribution_table.company_id.id,
        }

    def get_supply_point_id(self, code):
        supply_point_id = self.env["energy_selfconsumption.supply_point"].search_read(
            [("code", "=", code)], ["id"])
        if not supply_point_id:
            raise ValidationError(
                _("There isn't any supply point with this code: {code}").format(
                    code=code))
        return supply_point_id[0]["id"]

    def get_coefficient(self, coefficient):
        try:
            return fields.Float.convert_to_write(
                self=fields.Float(),
                value=coefficient,
                record=self.env[
                    "energy_selfconsumption.supply_point_assignation"].coefficient,
            )
        except ValueError:
            return 0

    def get_hour(self, hour):
        return hour

    def notification(self, subject, body):
        active_id = self.env.context.get("active_id")
        distribution_table = self.env[
            "energy_selfconsumption.distribution_table"].browse(active_id)
        distribution_table.notify_followers(subject=subject, body=body)
