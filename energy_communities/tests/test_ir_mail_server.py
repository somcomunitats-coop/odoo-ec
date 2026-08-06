from unittest.mock import patch

from cryptography.fernet import Fernet

from odoo.exceptions import UserError
from odoo.tests import common
from odoo.tests.common import tagged

from odoo.addons.energy_communities.models.ir_mail_server import (
    SMTP_PASS_ENCRYPTED_PREFIX,
)


@tagged("post_install", "-at_install")
class TestIrMailServerSmtpPassEncryption(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.MailServer = cls.env["ir.mail_server"]
        cls.plaintext_password = "MySecretSmtpPassword!"

    def _create_mail_server(self, password=None, **extra):
        vals = {
            "name": "Test SMTP Server",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_encryption": "starttls",
            "smtp_user": "user@example.com",
            "smtp_authentication": "login",
        }
        if password is not None:
            vals["smtp_pass"] = password
        vals.update(extra)
        return self.MailServer.create(vals)

    def _sql_get_passwords(self, server_id):
        # Flush pending ORM writes (inverse sets smtp_pass_encrypted in cache).
        self.env.flush_all()
        self.env.cr.execute(
            """
            SELECT smtp_pass, smtp_pass_encrypted
            FROM ir_mail_server
            WHERE id = %s
            """,
            (server_id,),
        )
        return self.env.cr.fetchone()

    def test_create_stores_encrypted_password_not_plaintext(self):
        server = self._create_mail_server(password=self.plaintext_password)

        smtp_pass_col, encrypted_col = self._sql_get_passwords(server.id)
        self.assertFalse(smtp_pass_col)
        self.assertTrue(encrypted_col)
        self.assertTrue(encrypted_col.startswith(SMTP_PASS_ENCRYPTED_PREFIX))
        self.assertNotIn(self.plaintext_password, encrypted_col)
        self.assertEqual(server.smtp_pass, self.plaintext_password)

    def test_write_updates_encrypted_password(self):
        server = self._create_mail_server(password="OldPassword")
        new_password = "NewPassword456"
        server.write({"smtp_pass": new_password})

        smtp_pass_col, encrypted_col = self._sql_get_passwords(server.id)
        self.assertFalse(smtp_pass_col)
        self.assertTrue(encrypted_col.startswith(SMTP_PASS_ENCRYPTED_PREFIX))
        self.assertNotIn(new_password, encrypted_col)
        self.assertEqual(server.smtp_pass, new_password)

    def test_write_empty_clears_encrypted_password(self):
        server = self._create_mail_server(password=self.plaintext_password)
        server.write({"smtp_pass": False})

        smtp_pass_col, encrypted_col = self._sql_get_passwords(server.id)
        self.assertFalse(smtp_pass_col)
        self.assertFalse(encrypted_col)
        self.assertFalse(server.smtp_pass)

    def test_encrypt_is_idempotent_for_already_encrypted_values(self):
        encrypted = self.MailServer._encrypt_smtp_pass(self.plaintext_password)
        again = self.MailServer._encrypt_smtp_pass(encrypted)
        self.assertEqual(encrypted, again)
        self.assertEqual(
            self.MailServer._decrypt_smtp_pass(again), self.plaintext_password
        )

    def test_copy_keeps_working_password(self):
        server = self._create_mail_server(password=self.plaintext_password)
        copy = server.copy({"name": "Copied SMTP Server"})
        self.assertEqual(copy.smtp_pass, self.plaintext_password)
        smtp_pass_col, encrypted_col = self._sql_get_passwords(copy.id)
        self.assertFalse(smtp_pass_col)
        self.assertTrue(encrypted_col.startswith(SMTP_PASS_ENCRYPTED_PREFIX))

    def test_connect_uses_decrypted_password(self):
        server = self._create_mail_server(password=self.plaintext_password)
        captured = {}

        def _fake_smtp_login(mail_server, connection, smtp_user, smtp_password):
            captured["smtp_user"] = smtp_user
            captured["smtp_password"] = smtp_password

        with patch.object(type(server), "_is_test_mode", return_value=False), patch(
            "odoo.addons.base.models.ir_mail_server.SMTPConnection"
        ) as mock_conn_cls, patch.object(
            type(server), "_smtp_login", autospec=True, side_effect=_fake_smtp_login
        ):
            mock_conn = mock_conn_cls.return_value
            mock_conn.starttls.return_value = None
            mock_conn.ehlo_or_helo_if_needed.return_value = None
            self.MailServer.connect(mail_server_id=server.id, allow_archived=True)

        self.assertEqual(captured["smtp_user"], "user@example.com")
        self.assertEqual(captured["smtp_password"], self.plaintext_password)

    def test_migrate_plaintext_passwords_from_legacy_column(self):
        from importlib.util import module_from_spec, spec_from_file_location
        from pathlib import Path

        server = self._create_mail_server(password=False)
        legacy_password = "LegacyPlainPassword"
        self.env.cr.execute(
            """
            UPDATE ir_mail_server
            SET smtp_pass = %s,
                smtp_pass_encrypted = NULL
            WHERE id = %s
            """,
            (legacy_password, server.id),
        )
        self.env.invalidate_all()

        migration_path = (
            Path(__file__).resolve().parents[1]
            / "migrations"
            / "16.0.0.8.2"
            / "post-encrypt_smtp_pass.py"
        )
        spec = spec_from_file_location("post_encrypt_smtp_pass", migration_path)
        migration_module = module_from_spec(spec)
        spec.loader.exec_module(migration_module)

        migrated = migration_module.migrate_plaintext_smtp_passwords(self.env)
        self.assertGreaterEqual(migrated, 1)

        server.invalidate_recordset(["smtp_pass", "smtp_pass_encrypted"])
        self.assertEqual(server.smtp_pass, legacy_password)

        smtp_pass_col, encrypted_col = self._sql_get_passwords(server.id)
        self.assertFalse(smtp_pass_col)
        self.assertTrue(encrypted_col.startswith(SMTP_PASS_ENCRYPTED_PREFIX))
        self.assertNotIn(legacy_password, encrypted_col)

        # Second run is a no-op
        self.assertEqual(migration_module.migrate_plaintext_smtp_passwords(self.env), 0)

    def test_decrypt_fails_gracefully_with_wrong_secret(self):
        server = self._create_mail_server(password=self.plaintext_password)
        encrypted = server.smtp_pass_encrypted
        wrong_fernet = Fernet(Fernet.generate_key())

        with patch.object(
            type(self.MailServer),
            "_get_smtp_pass_fernet",
            return_value=wrong_fernet,
        ):
            with self.assertRaises(UserError):
                self.MailServer._decrypt_smtp_pass(encrypted)
