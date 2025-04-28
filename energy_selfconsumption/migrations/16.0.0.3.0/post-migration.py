import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info("Starting post-migration from version %s.", version)
    logger.info("Old contracts reopened.")
    cr.execute(
        """
        UPDATE energy_selfconsumption_inscription_selfconsumption
            SET participation_assigned_quantity = participation_real_quantity;
        """
    )
    logger.info("Updated participation_assigned_quantity.")
    cr.execute(
        """
        UPDATE energy_selfconsumption_inscription_selfconsumption esis
            SET participation_real_quantity = espa.energy_shares
        FROM energy_selfconsumption_supply_point_assignation espa
        INNER JOIN energy_selfconsumption_distribution_table esdt
            ON espa.distribution_table_id = esdt.id
        WHERE esis.supply_point_id = espa.supply_point_id
            AND esdt.state = 'active'
            AND esdt.active = true
            AND esdt.selfconsumption_project_id = esis.selfconsumption_project_id;
        """
    )
    logger.info("Updated participation_real_quantity.")
    cr.execute(
        """
        UPDATE energy_selfconsumption_distribution_table
            SET date_start = now()
        WHERE state = 'active'
            AND active = true;
        """
    )
    logger.info("Updated date_start.")
    logger.info("Post migration completed.")
