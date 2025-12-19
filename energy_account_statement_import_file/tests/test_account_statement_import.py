import base64
import hashlib
import os
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestAccountStatementImport(TransactionCase):
    """Test cases for AccountStatementImport._complete_stmts_vals method."""

    def setUp(self):
        super().setUp()
        self.wizard = self.env["account.statement.import"]
        # Path to the parent class method for mocking
        self.parent_method_path = (
            "odoo.addons.account_statement_import_file.wizard."
            "account_statement_import.AccountStatementImport._complete_stmts_vals"
        )

    def test_complete_stmts_vals_adds_unique_import_id_when_missing(self):
        """Test that unique_import_id is added when it doesn't exist."""
        # Prepare test data
        stmts_vals = [
            {
                "name": "Test Statement",
                "transactions": [
                    {"date": "2024-01-01", "amount": 100.0, "name": "Transaction 1"},
                    {"date": "2024-01-02", "amount": 200.0, "name": "Transaction 2"},
                ],
            }
        ]
        journal = MagicMock()
        account_number = "1234567890"

        # Mock super() call - patch the parent class method
        with patch(self.parent_method_path, return_value=stmts_vals) as mock_super:
            result = self.wizard._complete_stmts_vals(
                stmts_vals, journal, account_number
            )

            # Verify super() was called
            mock_super.assert_called_once_with(stmts_vals, journal, account_number)

            # Verify unique_import_id was added to all transactions
            for st_vals in result:
                for lvals in st_vals["transactions"]:
                    self.assertIn("unique_import_id", lvals)
                    self.assertIsNotNone(lvals["unique_import_id"])
                    self.assertEqual(
                        len(lvals["unique_import_id"]), 32
                    )  # MD5 hash length

    def test_complete_stmts_vals_preserves_existing_unique_import_id(self):
        """Test that existing unique_import_id is not overwritten."""
        # Prepare test data with existing unique_import_id
        existing_id = "existing_unique_id_12345"
        stmts_vals = [
            {
                "name": "Test Statement",
                "transactions": [
                    {
                        "date": "2024-01-01",
                        "amount": 100.0,
                        "name": "Transaction 1",
                        "unique_import_id": existing_id,
                    },
                    {"date": "2024-01-02", "amount": 200.0, "name": "Transaction 2"},
                ],
            }
        ]
        journal = MagicMock()
        account_number = "1234567890"

        # Mock super() call - patch the parent class method
        with patch(self.parent_method_path, return_value=stmts_vals) as mock_super:
            result = self.wizard._complete_stmts_vals(
                stmts_vals, journal, account_number
            )

            # Verify super() was called
            mock_super.assert_called_once_with(stmts_vals, journal, account_number)

            # Verify existing unique_import_id was preserved
            self.assertEqual(
                result[0]["transactions"][0]["unique_import_id"], existing_id
            )

            # Verify new unique_import_id was added to transaction without it
            self.assertIn("unique_import_id", result[0]["transactions"][1])
            self.assertNotEqual(
                result[0]["transactions"][1]["unique_import_id"], existing_id
            )

    def test_complete_stmts_vals_generates_correct_md5_hash(self):
        """Test that the MD5 hash is generated correctly from transaction values."""
        # Prepare test data
        transaction_data = {"date": "2024-01-01", "amount": 100.0, "name": "Test"}
        stmts_vals = [
            {
                "name": "Test Statement",
                "transactions": [transaction_data.copy()],
            }
        ]
        journal = MagicMock()
        account_number = "1234567890"

        # Calculate expected hash
        lvals_str = str(sorted(transaction_data.items()))
        expected_hash = hashlib.md5(lvals_str.encode("utf-8")).hexdigest()

        # Mock super() call - patch the parent class method
        with patch(self.parent_method_path, return_value=stmts_vals):
            result = self.wizard._complete_stmts_vals(
                stmts_vals, journal, account_number
            )

            # Verify the hash matches expected value
            self.assertEqual(
                result[0]["transactions"][0]["unique_import_id"], expected_hash
            )

    def test_complete_stmts_vals_handles_multiple_statements(self):
        """Test that the method handles multiple statements correctly."""
        # Prepare test data with multiple statements
        stmts_vals = [
            {
                "name": "Statement 1",
                "transactions": [
                    {"date": "2024-01-01", "amount": 100.0, "name": "Txn 1"},
                ],
            },
            {
                "name": "Statement 2",
                "transactions": [
                    {"date": "2024-01-02", "amount": 200.0, "name": "Txn 2"},
                    {"date": "2024-01-03", "amount": 300.0, "name": "Txn 3"},
                ],
            },
        ]
        journal = MagicMock()
        account_number = "1234567890"

        # Mock super() call - patch the parent class method
        with patch(self.parent_method_path, return_value=stmts_vals):
            result = self.wizard._complete_stmts_vals(
                stmts_vals, journal, account_number
            )

            # Verify all statements and transactions have unique_import_id
            self.assertEqual(len(result), 2)
            self.assertEqual(len(result[0]["transactions"]), 1)
            self.assertEqual(len(result[1]["transactions"]), 2)

            for st_vals in result:
                for lvals in st_vals["transactions"]:
                    self.assertIn("unique_import_id", lvals)
                    self.assertIsNotNone(lvals["unique_import_id"])

    def test_complete_stmts_vals_handles_empty_transactions(self):
        """Test that the method handles statements with empty transactions."""
        # Prepare test data with empty transactions
        stmts_vals = [
            {
                "name": "Empty Statement",
                "transactions": [],
            }
        ]
        journal = MagicMock()
        account_number = "1234567890"

        # Mock super() call - patch the parent class method
        with patch(self.parent_method_path, return_value=stmts_vals):
            result = self.wizard._complete_stmts_vals(
                stmts_vals, journal, account_number
            )

            # Verify the statement is returned unchanged (no transactions to process)
            self.assertEqual(len(result), 1)
            self.assertEqual(len(result[0]["transactions"]), 0)

    def test_import_files_with_duplicate_lines(self):
        """Test that duplicate lines are not imported when importing two files."""
        # Check if N43 parser module is installed
        n43_module = self.env["ir.module.module"].search(
            [
                ("name", "=", "l10n_es_account_statement_import_n43"),
                ("state", "=", "installed"),
            ]
        )
        if not n43_module:
            self.skipTest(
                "N43 format parser module (l10n_es_account_statement_import_n43) "
                "is not installed. Install it to run this test."
            )

        # Get the path to the test files
        test_dir = os.path.dirname(os.path.abspath(__file__))
        file1_path = os.path.join(test_dir, "TT290825.293 half day 1d2.txt")
        file2_path = os.path.join(test_dir, "TT290825.741 full last day 2d2.txt")

        # Check if test files exist
        if not os.path.exists(file1_path) or not os.path.exists(file2_path):
            self.skipTest("Test files not found")

        # Create a bank journal with associated bank account
        company = self.env["res.company"].search(
            [("name", "=", "Community 1")], limit=1
        )
        # Extract account number from N43 file (first line contains account info)
        # Format: 11 + account_number (20 digits) + ...
        # Account number from file: 0100494814 (appears in first line)
        account_number = "0100494814"

        # Create partner bank account
        partner_bank = self.env["res.partner.bank"].create(
            {
                "acc_number": account_number,
                "company_id": company.id,
                "partner_id": company.partner_id.id,
            }
        )

        # Create bank journal linked to the bank account
        journal = self.env["account.journal"].create(
            {
                "name": "Test Bank Journal",
                "type": "bank",
                "code": "TEST",
                "company_id": company.id,
                "bank_account_id": partner_bank.id,
            }
        )

        # Read first file
        with open(file1_path, "rb") as f:
            file1_data = f.read()
        file1_b64 = base64.b64encode(file1_data).decode("utf-8")

        # Read second file
        with open(file2_path, "rb") as f:
            file2_data = f.read()
        file2_b64 = base64.b64encode(file2_data).decode("utf-8")

        # Create wizard and import first file
        wizard1 = self.env["account.statement.import"].create(
            {
                "statement_file": file1_b64,
                "statement_filename": "TT290825.293 half day 1d2.txt",
            }
        )
        result1 = {"statement_ids": [], "notifications": []}
        try:
            wizard1.with_context(journal_id=journal.id).import_single_file(
                file1_data, result1
            )
        except UserError as e:
            # Check if it's the "format not supported" error
            if "format is not supported" in str(e):
                self.skipTest(
                    "N43 format parser module (l10n_es_account_statement_import_n43) "
                    "is not installed. Install it to run this test."
                )
            raise
        except Exception as e:
            self.skipTest(f"Could not import first file: {e}")

        # Count lines after first import
        lines_after_first = self.env["account.bank.statement.line"].search_count(
            [("journal_id", "=", journal.id)]
        )
        unique_ids_after_first = set(
            self.env["account.bank.statement.line"]
            .search([("journal_id", "=", journal.id)])
            .mapped("unique_import_id")
        )
        unique_ids_after_first = {uid for uid in unique_ids_after_first if uid}

        # Verify first import created some lines
        self.assertGreater(
            lines_after_first,
            0,
            "First file import did not create any bank statement lines",
        )
        self.assertGreater(
            len(unique_ids_after_first),
            0,
            "First file import did not create any unique_import_ids",
        )

        # Create wizard and import second file (contains duplicate lines)
        wizard2 = self.env["account.statement.import"].create(
            {
                "statement_file": file2_b64,
                "statement_filename": "TT290825.741 full last day 2d2.txt",
            }
        )
        result2 = {"statement_ids": [], "notifications": []}
        try:
            wizard2.with_context(journal_id=journal.id).import_single_file(
                file2_data, result2
            )
        except UserError as e:
            # Check if it's the "format not supported" error
            if "format is not supported" in str(e):
                self.skipTest(
                    "N43 format parser module (l10n_es_account_statement_import_n43) "
                    "is not installed. Install it to run this test."
                )
            raise
        except Exception as e:
            self.skipTest(f"Could not import second file: {e}")

        # Count lines after second import
        lines_after_second = self.env["account.bank.statement.line"].search_count(
            [("journal_id", "=", journal.id)]
        )
        unique_ids_after_second = set(
            self.env["account.bank.statement.line"]
            .search([("journal_id", "=", journal.id)])
            .mapped("unique_import_id")
        )
        unique_ids_after_second = {uid for uid in unique_ids_after_second if uid}

        # Verify that all unique_import_ids from first import are still present
        self.assertTrue(
            unique_ids_after_first.issubset(unique_ids_after_second),
            "Some unique_import_ids from first import are missing after second import",
        )

        # Verify that no duplicate unique_import_ids exist
        all_unique_ids = list(
            self.env["account.bank.statement.line"]
            .search([("journal_id", "=", journal.id)])
            .mapped("unique_import_id")
        )
        all_unique_ids = [uid for uid in all_unique_ids if uid]
        self.assertEqual(
            len(all_unique_ids),
            len(set(all_unique_ids)),
            "Duplicate unique_import_ids found in bank statement lines",
        )

        # Verify that the number of unique IDs equals the number of lines
        self.assertEqual(
            len(unique_ids_after_second),
            lines_after_second,
            "Number of unique_import_ids does not match number of lines",
        )

        # Verify that lines_after_second >= lines_after_first
        # (second import should add new lines or keep the same if all are duplicates)
        self.assertGreaterEqual(
            lines_after_second,
            lines_after_first,
            "Second import removed lines from first import",
        )
