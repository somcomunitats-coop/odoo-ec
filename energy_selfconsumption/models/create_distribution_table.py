import logging
from datetime import datetime

from stdnum.es import iban

from odoo import _, models

logger = logging.getLogger(__name__)


class CreateDistributionTable(models.AbstractModel):
    _name = "energy_selfconsumption.create_distribution_table"
    _description = "Service to create distribution table for a self-consumption"

    def create_energy_selfconsumption_supply_point_assignation_sql(
        self, values_list, distribution_table
    ):
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
                distribution_table.id,
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
        if "null" in str(data):
            logger.error("Error query:" + query)
        else:
            try:
                self.env.cr.execute(query, data)
                self.env.cr.commit()
            except Exception as e:
                self.env.cr.rollback()
                error = True
                logger.error(f"\n\n SQL: \n {query}")
                logger.error(f"Error executing bulk insert query: {e}")
                self.notification(
                    distribution_table, "Error query", f"Query: {query}\nError: {e}"
                )

        if not error:
            self.notification(
                distribution_table,
                "Distribution table",
                "Distribution table create successfully",
            )

    def notification(self, distribution_table, subject, body):
        try:
            distribution_table.message_post(
                body=body,
                subject=subject,
                message_type="notification",
                subtype_xmlid="mail.mt_comment",
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
