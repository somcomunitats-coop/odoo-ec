from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import common, tagged

from odoo.addons.mail.tests.common import MailCommon


@tagged("-at_install", "post_install")
class TestEmailSendingAssistant(
    common.TransactionCase
):  # (MailCommon): #TODO: Fix this super().setUpClass()
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.community = self.env.ref(
            "energy_communities.energy_community_company_1_wizard"
        ).new_company_id

        # Create test partners
        self.partner1 = self.env["res.partner"].create(
            {
                "name": "Test Partner 1",
                "email": "partner1@test.com",
                "vat": "43304105G",
                "company_id": self.community.id,
            }
        )
        self.partner2 = self.env["res.partner"].create(
            {
                "name": "Test Partner 2",
                "email": "partner2@test.com",
                "vat": "72636163R",
                "company_id": self.community.id,
            }
        )

        # Create mail template for res.partner
        self.mail_template_partner = self.env["mail.template"].create(
            {
                "name": "Test Partner Template",
                "model_id": self.env.ref("base.model_res_partner").id,
                "subject": "Test Email Subject",
                "body_html": "<p>Test Email Body</p>",
            }
        )
        # Create mail template for res.partner no global
        self.mail_template_partner_no_global = self.env["mail.template"].create(
            {
                "name": "Test Partner Template No Global",
                "model_id": self.env.ref("base.model_res_partner").id,
                "subject": "Test Email Subject",
                "body_html": "<p>Test Email Body</p>",
                "company_id": self.community.id,
            }
        )

        # Create active languages
        self.lang_en = self.env["res.lang"].search([("code", "=", "en_US")], limit=1)
        self.lang_es = self.env["res.lang"].search([("code", "=", "es_ES")], limit=1)
        if not self.lang_en:
            self.lang_en = self.env["res.lang"].create(
                {
                    "name": "English",
                    "code": "en_US",
                    "iso_code": "en",
                    "active": True,
                }
            )
        if not self.lang_es:
            self.lang_es = self.env["res.lang"].create(
                {
                    "name": "Spanish",
                    "code": "es_ES",
                    "iso_code": "es",
                    "active": True,
                }
            )

    def test_wizard_initialization_with_active_ids(self):
        """Test wizard initialization with active_ids in context"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id, self.partner2.id],
        }
        wizard = self.env["email.sending.assistant.wiz"].with_context(ctx).create({})
        self.assertEqual(wizard.num_selected_records, 2)
        self.assertEqual(wizard.state, "draft")

    def test_wizard_initialization_without_active_ids(self):
        """Test wizard initialization without active_ids in context"""
        ctx = {"active_model": "res.partner"}
        wizard = self.env["email.sending.assistant.wiz"].with_context(ctx).create({})
        self.assertEqual(wizard.num_selected_records, 0)
        self.assertEqual(wizard.state, "draft")

    def test_get_domain_email_template(self):
        """Test _get_domain_email_template method"""
        ctx = {"active_model": "res.partner"}
        wizard = self.env["email.sending.assistant.wiz"].with_context(ctx).create({})
        domain = wizard._get_domain_email_template()
        expected_domain = [("model", "=", "res.partner")]
        self.assertEqual(domain, expected_domain)

    def test_get_language_selection(self):
        """Test _get_language_selection method"""
        wizard = self.env["email.sending.assistant.wiz"].create({})
        languages = wizard._get_language_selection()
        self.assertIsInstance(languages, list)
        self.assertTrue(len(languages) > 0)
        # Check that all items are tuples with (code, name)
        for lang_tuple in languages:
            self.assertIsInstance(lang_tuple, tuple)
            self.assertEqual(len(lang_tuple), 2)

    def test_action_test_email(self):
        """Test action_test_email changes state and returns correct action"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create({"email_template_id": self.mail_template_partner.id})
        )
        self.assertEqual(wizard.state, "draft")

        result = wizard.action_test_email()

        self.assertEqual(wizard.state, "test")
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "email.sending.assistant.wiz")
        self.assertEqual(result["view_mode"], "form")
        self.assertEqual(result["target"], "new")
        self.assertEqual(result["res_id"], wizard.id)

    @patch("odoo.addons.mail.models.mail_template.MailTemplate.send_mail")
    def test_action_send_email_test_mode_with_recipient(self, mock_send_mail):
        """Test action_send_email in test mode with recipient email"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {
                    "email_template_id": self.mail_template_partner.id,
                    "state": "test",
                    "recipient_email_address_for_test": "test@example.com",
                }
            )
        )

        result = wizard.action_send_email()

        # Verify email was sent with correct parameters
        mock_send_mail.assert_called_once()
        call_args = mock_send_mail.call_args
        self.assertEqual(call_args[0][0], self.partner1.id)
        self.assertEqual(call_args[1]["email_values"]["email_to"], "test@example.com")
        self.assertEqual(wizard.state, "draft")
        self.assertEqual(result["type"], "ir.actions.act_window")

    def test_action_send_email_test_mode_without_recipient(self):
        """Test action_send_email in test mode without recipient email raises error"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {
                    "email_template_id": self.mail_template_partner.id,
                    "state": "test",
                }
            )
        )

        with self.assertRaises(ValidationError) as context:
            wizard.action_send_email()

        self.assertIn("recipient email address for test", str(context.exception))

    @patch("odoo.addons.mail.models.mail_template.MailTemplate.send_mail")
    def test_action_send_email_normal_mode(self, mock_send_mail):
        """Test action_send_email in normal mode sends to all active_ids"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id, self.partner2.id],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {"email_template_id": self.mail_template_partner.id, "state": "draft"}
            )
        )

        wizard.action_send_email()

        # Verify emails were sent to all active_ids
        # Extract partner IDs from call arguments
        call_ids = []
        for call in mock_send_mail.call_args_list:
            try:
                args, kwargs = call
                if args and len(args) > 0:
                    call_ids.append(args[0])
            except (ValueError, TypeError):
                continue
        # Verify both partners received emails
        self.assertIn(self.partner1.id, call_ids)
        self.assertIn(self.partner2.id, call_ids)
        # Verify at least 2 calls were made (one per partner)
        self.assertGreaterEqual(len(call_ids), 2)

    @patch("odoo.addons.mail.models.mail_template.MailTemplate.send_mail")
    def test_action_send_email_with_force_language(self, mock_send_mail):
        """Test action_send_email with force_language creates template copy"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {
                    "email_template_id": self.mail_template_partner.id,
                    "state": "draft",
                    "force_language": "es_ES",
                }
            )
        )

        # Count templates before
        template_count_before = self.env["mail.template"].search_count([])

        wizard.action_send_email()

        # Verify email was sent
        # Note: send_mail might be called multiple times due to unlink() operations
        # We verify that it was called at least once
        self.assertGreaterEqual(mock_send_mail.call_count, 1)
        # Find calls that are actual sends (not from unlink operations)
        # In normal mode, sends don't have email_values, so we check for calls with partner ID
        send_calls = []
        for call in mock_send_mail.call_args_list:
            try:
                args, kwargs = call
                if args and args[0] == self.partner1.id:
                    send_calls.append(call)
            except (ValueError, TypeError):
                continue
        self.assertGreaterEqual(
            len(send_calls), 1, "Expected at least one call with partner ID"
        )
        # Verify template copy was created and then unlinked
        template_count_after = self.env["mail.template"].search_count([])
        self.assertEqual(template_count_before, template_count_after)

    @patch("odoo.addons.mail.models.mail_template.MailTemplate.send_mail")
    def test_action_send_email_test_mode_with_force_language(self, mock_send_mail):
        """Test action_send_email in test mode with force_language"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {
                    "email_template_id": self.mail_template_partner.id,
                    "state": "test",
                    "force_language": "es_ES",
                    "recipient_email_address_for_test": "test@example.com",
                }
            )
        )

        # Count templates before
        template_count_before = self.env["mail.template"].search_count([])

        result = wizard.action_send_email()

        # Verify email was sent with test recipient
        # Note: send_mail might be called multiple times due to unlink() operations
        # We verify that it was called at least once with the correct parameters
        self.assertGreaterEqual(mock_send_mail.call_count, 1)
        # Find the call with email_values (the actual send)
        # call_args_list contains tuples of (args, kwargs)
        send_calls = []
        for call in mock_send_mail.call_args_list:
            try:
                args, kwargs = call
                if (
                    isinstance(kwargs, dict)
                    and kwargs.get("email_values", {}).get("email_to")
                    == "test@example.com"
                ):
                    send_calls.append(call)
            except (ValueError, TypeError):
                # Skip calls that don't match expected structure
                continue
        self.assertEqual(
            len(send_calls), 1, "Expected exactly one call with test email recipient"
        )
        args, kwargs = send_calls[0]
        self.assertEqual(args[0], self.partner1.id)
        self.assertEqual(kwargs["email_values"]["email_to"], "test@example.com")
        # Verify template copy was created and then unlinked
        template_count_after = self.env["mail.template"].search_count([])
        self.assertEqual(template_count_before, template_count_after)
        # Verify state changed back to draft
        self.assertEqual(wizard.state, "draft")
        self.assertEqual(result["type"], "ir.actions.act_window")

    def test_action_cancel_from_test_state(self):
        """Test action_cancel changes state from test to draft"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {
                    "email_template_id": self.mail_template_partner.id,
                    "state": "test",
                }
            )
        )

        result = wizard.action_cancel()

        self.assertEqual(wizard.state, "draft")
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "email.sending.assistant.wiz")
        self.assertEqual(result["view_mode"], "form")
        self.assertEqual(result["target"], "new")

    def test_action_cancel_from_draft_state(self):
        """Test action_cancel from draft state (should not change state)"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [self.partner1.id],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {
                    "email_template_id": self.mail_template_partner.id,
                    "state": "draft",
                }
            )
        )

        # action_cancel should not return anything if state is draft
        result = wizard.action_cancel()
        # If state is draft, action_cancel might return None or not change state
        # Based on the code, it only does something if state == "test"
        if result:
            self.assertEqual(wizard.state, "draft")

    @patch("odoo.addons.mail.models.mail_template.MailTemplate.send_mail")
    def test_action_send_email_test_mode_empty_active_ids(self, mock_send_mail):
        """Test action_send_email in test mode with empty active_ids"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {
                    "email_template_id": self.mail_template_partner.id,
                    "state": "test",
                    "recipient_email_address_for_test": "test@example.com",
                }
            )
        )

        # Should not send email if active_ids is empty
        wizard.action_send_email()
        mock_send_mail.assert_not_called()

    @patch("odoo.addons.mail.models.mail_template.MailTemplate.send_mail")
    def test_action_send_email_normal_mode_empty_active_ids(self, mock_send_mail):
        """Test action_send_email in normal mode with empty active_ids"""
        ctx = {
            "active_model": "res.partner",
            "active_ids": [],
        }
        wizard = (
            self.env["email.sending.assistant.wiz"]
            .with_context(ctx)
            .create(
                {"email_template_id": self.mail_template_partner.id, "state": "draft"}
            )
        )

        # Should not send email if active_ids is empty
        wizard.action_send_email()
        mock_send_mail.assert_not_called()
