import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(f"Starting migration from version {version}.")
    cr.execute("DELETE FROM website_visitor;")
    _logger.info("Migration completed.")
