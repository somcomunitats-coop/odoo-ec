import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(
        "Starting pre-migration from version %s to remove voluntary_share_id.",
        version,
    )
    cr.execute(
        """
        DELETE FROM ir_model_fields
        WHERE model IN ('res.company', 'res.config.settings')
          AND name = 'voluntary_share_id'
        """
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
        WHERE module = 'energy_communities_cooperator'
          AND name IN (
              'field_res_company__voluntary_share_id',
              'field_res_config_settings__voluntary_share_id',
              'field_res_config_settings_energy_communities__voluntary_share_id'
          )
        """
    )
    cr.execute(
        """
        DELETE FROM ir_translation
        WHERE name IN (
            'res.company,voluntary_share_id',
            'res.config.settings,voluntary_share_id'
        )
        """
    )
    cr.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'res_company'
                  AND column_name = 'voluntary_share_id'
            ) THEN
                ALTER TABLE res_company DROP COLUMN voluntary_share_id;
            END IF;
        END $$;
        """
    )
    _logger.info("Removed legacy res.company.voluntary_share_id traces.")
