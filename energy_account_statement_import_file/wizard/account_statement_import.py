import hashlib

from odoo import models


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        """
        Override to add unique_import_id to the statement values.
        This is used to avoid duplicates when importing statements.
        """
        stmts_vals = super()._complete_stmts_vals(stmts_vals, journal, account_number)
        unique_import_ids = []
        for st_vals in stmts_vals:
            for lvals in st_vals["transactions"]:
                if not lvals.get("unique_import_id", False):
                    # Create MD5 hash from all values in st_vals
                    lvals_str = str(sorted(lvals.items()))
                    lvals_hash = hashlib.md5(lvals_str.encode("utf-8")).hexdigest()
                    if lvals_hash in unique_import_ids:
                        lvals_hash = hashlib.md5(
                            (lvals_str + str(len(unique_import_ids))).encode("utf-8")
                        ).hexdigest()
                    lvals["unique_import_id"] = lvals_hash
                    unique_import_ids.append(lvals_hash)
        return stmts_vals
