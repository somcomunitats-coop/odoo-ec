import logging
from datetime import datetime

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

# Constants for bulk operations
BULK_INSERT_BATCH_SIZE = 1000
MAX_RETRY_ATTEMPTS = 3


class CreateDistributionTable(models.AbstractModel):
    """
    Distribution Table Creation Service

    This abstract model provides services for creating and managing
    distribution tables for self-consumption projects, including:
    - Bulk creation of supply point assignations
    - SQL-based bulk insert operations for performance
    - Error handling and notification management
    - Transaction management and rollback capabilities
    """

    _name = "energy_selfconsumption.create_distribution_table"
    _description = "Service to create distribution table for a self-consumption"

    def create_energy_selfconsumption_supply_point_assignation_sql(
        self, values_list, distribution_table
    ):
        """
        Create supply point assignations using bulk SQL insert

        This method performs bulk insertion of supply point assignations
        for improved performance when dealing with large datasets.

        Args:
            values_list (list): List of dictionaries containing assignation data
            distribution_table: Distribution table record to assign points to

        Returns:
            bool: True if successful, False if errors occurred
        """
        if not values_list:
            _logger.warning("No values provided for supply point assignation creation")
            return False

        if not distribution_table:
            _logger.error("Distribution table is required for assignation creation")
            return False

        try:
            self._validate_assignation_values(values_list)
            success = self._execute_bulk_insert(values_list, distribution_table)

            if success:
                self._send_success_notification(distribution_table, len(values_list))

            return success

        except ValidationError as e:
            _logger.error(f"Validation error in assignation creation: {e}")
            self._send_error_notification(
                distribution_table, "Validation Error", str(e)
            )
            return False
        except Exception as e:
            _logger.error(f"Unexpected error in assignation creation: {e}")
            self._send_error_notification(
                distribution_table, "Unexpected Error", str(e)
            )
            return False

    def create_energy_selfconsumption_supply_point_assignation(
        self, values_list, distribution_table
    ):
        """
        Create supply point assignations using bulk SQL insert

        This method performs bulk insertion of supply point assignations
        for improved performance when dealing with large datasets.

        Args:
            values_list (list): List of dictionaries containing assignation data
            distribution_table: Distribution table record to assign points to

        Returns:
            bool: True if successful, False if errors occurred
        """
        if not values_list:
            _logger.warning("No values provided for supply point assignation creation")
            return False

        if not distribution_table:
            _logger.error("Distribution table is required for assignation creation")
            return False

        try:
            self._validate_assignation_values(values_list)
            success = self._create_energy_selfconsumption_supply_point_assignation(
                values_list, distribution_table
            )

            if success:
                self._send_success_notification(distribution_table, len(values_list))

            return success

        except ValidationError as e:
            _logger.error(f"Validation error in assignation creation: {e}")
            self._send_error_notification(
                distribution_table, "Validation Error", str(e)
            )
            return False
        except Exception as e:
            _logger.error(f"Unexpected error in assignation creation: {e}")
            self._send_error_notification(
                distribution_table, "Unexpected Error", str(e)
            )
            return False

    def _validate_assignation_values(self, values_list):
        """
        Validate assignation values before bulk insert

        Args:
            values_list (list): List of assignation value dictionaries

        Raises:
            ValidationError: If validation fails
        """
        required_fields = [
            "supply_point_id",
            "coefficient",
            "energy_shares",
            "company_id",
        ]

        for i, values in enumerate(values_list):
            # Check required fields
            for field in required_fields:
                if field not in values or values[field] is None:
                    raise ValidationError(
                        _(
                            "Missing required field '{field}' in assignation {index}"
                        ).format(field=field, index=i + 1)
                    )

            # Validate coefficient range
            coefficient = float(values["coefficient"])
            if coefficient < 0 or coefficient > 1:
                raise ValidationError(
                    _(
                        "Invalid coefficient value {coefficient} in assignation {index}. Must be between 0 and 1."
                    ).format(coefficient=coefficient, index=i + 1)
                )

            # Validate energy shares
            energy_shares = float(values["energy_shares"])
            if energy_shares < 0:
                raise ValidationError(
                    _(
                        "Invalid energy shares value {energy_shares} in assignation {index}. Must be positive."
                    ).format(energy_shares=energy_shares, index=i + 1)
                )

    def _execute_bulk_insert(self, values_list, distribution_table):
        """
        Execute the bulk SQL insert operation

        Args:
            values_list (list): Validated assignation values
            distribution_table: Distribution table record

        Returns:
            bool: True if successful, False otherwise
        """
        # Define table columns for insert
        columns = [
            "distribution_table_id",
            "supply_point_id",
            "coefficient",
            "energy_shares",
            "company_id",
            "create_uid",
            "create_date",
            "write_uid",
            "write_date",
        ]

        # Prepare data tuples
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_user_id = self.env.user.id

        data = []
        for values in values_list:
            data_tuple = (
                distribution_table.id,
                values["supply_point_id"],
                float(values["coefficient"]),
                float(values["energy_shares"]),
                values["company_id"],
                current_user_id,
                current_time,
                current_user_id,
                current_time,
            )
            data.append(data_tuple)

        # Build SQL query
        table_name = "energy_selfconsumption_supply_point_assignation"
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        query = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
        """

        # Execute bulk insert with transaction management
        try:
            # Process in batches for large datasets
            for i in range(0, len(data), BULK_INSERT_BATCH_SIZE):
                batch = data[i : i + BULK_INSERT_BATCH_SIZE]

                # Check for null values in batch
                if self._contains_null_values(batch):
                    _logger.error(
                        f"Null values detected in batch {i // BULK_INSERT_BATCH_SIZE + 1}"
                    )
                    return False

                # Execute batch insert
                self.env.cr.executemany(query, batch)
                _logger.info(
                    f"Inserted batch {i // BULK_INSERT_BATCH_SIZE + 1} with {len(batch)} records"
                )

            # Commit transaction
            self.env.cr.commit()
            _logger.info(f"Successfully inserted {len(data)} supply point assignations")
            return True

        except Exception as e:
            # Rollback on error
            self.env.cr.rollback()
            _logger.error(f"SQL execution failed: {e}")
            _logger.error(f"Query: {query}")
            _logger.error(f"Sample data: {data[:3] if data else 'No data'}")

            self._send_error_notification(
                distribution_table,
                "SQL Execution Error",
                f"Query: {query}\nError: {str(e)}",
            )
            return False

    def _create_energy_selfconsumption_supply_point_assignation(
        self, values_list, distribution_table
    ):
        """
        Create supply point assignations using bulk SQL insert

        Args:
            values_list (list): Validated assignation values
            distribution_table: Distribution table record

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for values in values_list:
                self.env["energy_selfconsumption.supply_point_assignation"].create(
                    {
                        "distribution_table_id": distribution_table.id,
                        "supply_point_id": values["supply_point_id"],
                        "coefficient": float(values["coefficient"]),
                        "energy_shares": float(values["energy_shares"]),
                        "company_id": values["company_id"],
                    }
                )
            return True
        except Exception as e:
            _logger.error(f"Error creating supply point assignations: {e}")
            return False

    def _contains_null_values(self, data_batch):
        """
        Check if data batch contains null values

        Args:
            data_batch (list): Batch of data tuples

        Returns:
            bool: True if null values found, False otherwise
        """
        for data_tuple in data_batch:
            if any(value is None for value in data_tuple):
                return True
        return False

    def _send_success_notification(self, distribution_table, record_count):
        """
        Send success notification to distribution table

        Args:
            distribution_table: Distribution table record
            record_count (int): Number of records created
        """
        message = _(
            "Distribution table created successfully with {count} supply point assignations"
        ).format(count=record_count)

        self._send_notification(
            distribution_table, _("Distribution Table Created"), message, "success"
        )

    def _send_error_notification(self, distribution_table, subject, error_message):
        """
        Send error notification to distribution table

        Args:
            distribution_table: Distribution table record
            subject (str): Error subject
            error_message (str): Detailed error message
        """
        self._send_notification(distribution_table, subject, error_message, "error")

    def _send_notification(
        self, distribution_table, subject, body, notification_type="info"
    ):
        """
        Send notification message to distribution table

        Args:
            distribution_table: Distribution table record
            subject (str): Message subject
            body (str): Message body
            notification_type (str): Type of notification (info, success, error)
        """
        try:
            # Determine message subtype based on notification type
            subtype_mapping = {
                "error": "mail.mt_comment",
                "success": "mail.mt_note",
                "info": "mail.mt_comment",
            }

            subtype = subtype_mapping.get(notification_type, "mail.mt_comment")

            distribution_table.message_post(
                body=body,
                subject=subject,
                message_type="notification",
                subtype_xmlid=subtype,
            )

            _logger.info(
                f"Notification sent to distribution table {distribution_table.id}: {subject}"
            )

        except Exception as e:
            _logger.error(f"Failed to send notification: {e}")
            _logger.error(f"Subject: {subject}, Body: {body}")

    def create_distribution_table_with_assignations(
        self, project_id, assignation_data, table_type="fixed"
    ):
        """
        Create a complete distribution table with assignations

        High-level method that creates a distribution table and populates it
        with supply point assignations in a single transaction.

        Args:
            project_id (int): Self-consumption project ID
            assignation_data (list): List of assignation dictionaries
            table_type (str): Type of distribution table ('fixed' or 'hourly')

        Returns:
            distribution_table: Created distribution table record or False
        """
        try:
            # Create distribution table
            distribution_table = self.env[
                "energy_selfconsumption.distribution_table"
            ].create(
                {
                    "selfconsumption_project_id": project_id,
                    "type": table_type,
                }
            )

            # Create assignations
            success = self.create_energy_selfconsumption_supply_point_assignation(
                assignation_data, distribution_table
            )

            if success:
                _logger.info(
                    f"Created distribution table {distribution_table.id} with {len(assignation_data)} assignations"
                )
                return distribution_table
            else:
                # Clean up on failure
                distribution_table.unlink()
                return False

        except Exception as e:
            _logger.error(f"Failed to create distribution table with assignations: {e}")
            return False

    def validate_coefficient_sum(self, assignation_data):
        """
        Validate that coefficients sum to 1.0 for fixed distribution tables

        Args:
            assignation_data (list): List of assignation dictionaries

        Returns:
            bool: True if valid, False otherwise

        Raises:
            ValidationError: If coefficient sum is invalid
        """
        total_coefficient = sum(float(data["coefficient"]) for data in assignation_data)

        # Allow small floating point precision errors
        tolerance = 0.000001

        if abs(total_coefficient - 1.0) > tolerance:
            raise ValidationError(
                _(
                    "Total coefficient sum is {total}, but must equal 1.0 for fixed distribution tables"
                ).format(total=round(total_coefficient, 6))
            )

        return True

    def get_assignation_statistics(self, assignation_data):
        """
        Get statistics about assignation data

        Args:
            assignation_data (list): List of assignation dictionaries

        Returns:
            dict: Statistics dictionary
        """
        if not assignation_data:
            return {
                "count": 0,
                "total_coefficient": 0.0,
                "total_energy_shares": 0.0,
                "avg_coefficient": 0.0,
                "min_coefficient": 0.0,
                "max_coefficient": 0.0,
            }

        coefficients = [float(data["coefficient"]) for data in assignation_data]
        energy_shares = [float(data["energy_shares"]) for data in assignation_data]

        return {
            "count": len(assignation_data),
            "total_coefficient": sum(coefficients),
            "total_energy_shares": sum(energy_shares),
            "avg_coefficient": sum(coefficients) / len(coefficients),
            "min_coefficient": min(coefficients),
            "max_coefficient": max(coefficients),
        }
