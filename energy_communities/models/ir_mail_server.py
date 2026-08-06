import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Prefix marks values encrypted by this module (Fernet tokens are not re-encrypted).
SMTP_PASS_ENCRYPTED_PREFIX = "ecenc$"


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    smtp_pass = fields.Char(
        string="Password",
        compute="_compute_smtp_pass",
        inverse="_inverse_smtp_pass",
        store=False,
        readonly=False,
        help="Optional password for SMTP authentication",
        groups="base.group_system",
    )
    smtp_pass_encrypted = fields.Char(
        string="Encrypted Password",
        groups="base.group_system",
        copy=True,
    )

    @api.depends("smtp_pass_encrypted")
    def _compute_smtp_pass(self):
        for server in self:
            server.smtp_pass = self._decrypt_smtp_pass(server.smtp_pass_encrypted)

    def _inverse_smtp_pass(self):
        for server in self:
            server.smtp_pass_encrypted = self._encrypt_smtp_pass(server.smtp_pass)

    @api.model
    def _get_smtp_pass_fernet(self):
        # database.secret is always initialized by Odoo (ir.config_parameter defaults).
        secret = self.env["ir.config_parameter"].sudo().get_param("database.secret")
        if not secret:
            raise UserError(
                _("Database secret is missing; cannot encrypt SMTP passwords.")
            )
        key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
        return Fernet(key)

    @api.model
    def _encrypt_smtp_pass(self, plaintext):
        if not plaintext:
            return False
        if isinstance(plaintext, bytes):
            plaintext = plaintext.decode("utf-8")
        if plaintext.startswith(SMTP_PASS_ENCRYPTED_PREFIX):
            return plaintext
        token = (
            self._get_smtp_pass_fernet()
            .encrypt(plaintext.encode("utf-8"))
            .decode("utf-8")
        )
        return f"{SMTP_PASS_ENCRYPTED_PREFIX}{token}"

    @api.model
    def _decrypt_smtp_pass(self, ciphertext):
        if not ciphertext:
            return False
        if isinstance(ciphertext, bytes):
            ciphertext = ciphertext.decode("utf-8")
        if not ciphertext.startswith(SMTP_PASS_ENCRYPTED_PREFIX):
            # Legacy plaintext accidentally stored in the encrypted column
            return ciphertext
        token = ciphertext[len(SMTP_PASS_ENCRYPTED_PREFIX) :]
        try:
            return (
                self._get_smtp_pass_fernet()
                .decrypt(token.encode("utf-8"))
                .decode("utf-8")
            )
        except InvalidToken as exc:
            _logger.exception("Failed to decrypt SMTP password")
            raise UserError(
                _(
                    "Could not decrypt SMTP password. "
                    "The database secret may have changed."
                )
            ) from exc
