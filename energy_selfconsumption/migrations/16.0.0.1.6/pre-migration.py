import logging

logger = logging.getLogger(__name__)


def migrate(cr, version):
    logger.info(f"Starting pre-migration from version {version}.")
    cr.execute(
        """ALTER TABLE IF EXISTS energy_project_participation RENAME TO energy_selfconsumptions_participation;"""
    )
    logger.info(
        "Renamed energy_project_participation to energy_selfconsumptions_participation."
    )
    cr.execute(
        """
        DO $$
        BEGIN
          IF EXISTS(SELECT *
            FROM information_schema.columns
            WHERE table_name='energy_selfconsumption_inscription_selfconsumption' and column_name='participation')
          THEN
              ALTER TABLE energy_selfconsumption_inscription_selfconsumption RENAME COLUMN participation TO participation_id;
          END IF;
        END $$;
        """
    )
    logger.info("Renamed column participation to participation_id.")
    logger.info("Pre migration completed.")
