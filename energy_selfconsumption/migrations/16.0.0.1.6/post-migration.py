import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info(f"Starting post-migration from version {version}.")
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
    logger.info("Post migration completed.")
