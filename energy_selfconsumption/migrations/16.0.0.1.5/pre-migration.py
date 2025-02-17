import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info(f"Starting migration from version {version}.")
    cr.execute(
        """ALTER TABLE energy_project_participation RENAME TO energy_selfconsumptions_participation;"""
    )
    logger.info(
        "Renamed energy_project_participation to energy_selfconsumptions_participation."
    )
    cr.execute(
        """ALTER TABLE energy_selfconsumption_inscription_selfconsumption RENAME COLUMN participation TO participation_id;"""
    )
    logger.info("Renamed column participation to participation_id.")
    cr.execute(
        """update energy_selfconsumption_inscription_selfconsumption set participation_real_quantity = (
                    select quantity from energy_selfconsumptions_participation where id = participation_id
                );"""
    )
    logger.info("Updated participation_real_quantity.")
    cr.execute(
        """update energy_selfconsumption_inscription_selfconsumption set state = 'active' where supply_point_id in (
                    select supply_point_id from energy_selfconsumption_supply_point_assignation where distribution_table_id in (
                        select id from energy_selfconsumption_distribution_table where state = 'active' and active = true
                        and selfconsumption_project_id = energy_selfconsumption_inscription_selfconsumption.selfconsumption_project_id
                    )
                );"""
    )
    logger.info("Updated state.")
    logger.info("Migration completed.")
