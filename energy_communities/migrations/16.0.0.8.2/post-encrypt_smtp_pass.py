import logging

from odoo import SUPERUSER_ID, api

logger = logging.getLogger(__name__)


def migrate_plaintext_smtp_passwords(env):
    """Move plaintext values from smtp_pass into smtp_pass_encrypted and clear them.

    Idempotent: only processes rows with a non-empty legacy smtp_pass column.
    """
    cr = env.cr
    mail_server = env["ir.mail_server"]
    cr.execute(
        """
        SELECT id, smtp_pass
        FROM ir_mail_server
        WHERE smtp_pass IS NOT NULL
          AND TRIM(smtp_pass) != ''
        """
    )
    rows = cr.fetchall()
    if not rows:
        cr.execute(
            """
            UPDATE ir_mail_server
            SET smtp_pass = NULL
            WHERE smtp_pass IS NOT NULL
              AND smtp_pass_encrypted IS NOT NULL
              AND smtp_pass_encrypted != ''
            """
        )
        return 0

    migrated = 0
    for server_id, plaintext in rows:
        encrypted = mail_server._encrypt_smtp_pass(plaintext)
        cr.execute(
            """
            UPDATE ir_mail_server
            SET smtp_pass_encrypted = %s,
                smtp_pass = NULL
            WHERE id = %s
            """,
            (encrypted, server_id),
        )
        migrated += 1
    logger.info(
        "Encrypted %s outgoing mail server password(s) in ir.mail_server",
        migrated,
    )
    return migrated


def migrate(cr, version):
    logger.info(
        "Encrypting existing ir.mail_server smtp_pass values (from %s)", version
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    migrated = migrate_plaintext_smtp_passwords(env)
    logger.info("Encrypted %s outgoing mail server password(s)", migrated)
