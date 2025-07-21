from odoo import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _compute_running_balance(self):
        """Override to handle NewId records safely"""
        # Filter out records with NewId to avoid CacheMiss
        valid_records = self.filtered(lambda r: r.id and not str(r.id).startswith('NewId'))
        
        if not valid_records:
            # Set default value for new records
            for record in self:
                record.running_balance = 0.0
            return
        
        # Call original method only for valid records
        super(AccountBankStatementLine, valid_records)._compute_running_balance()
        
        # Set default value for new records
        for record in self - valid_records:
            record.running_balance = 0.0

    def _compute_internal_index(self):
        """Override to handle NewId records safely"""
        # Filter out records with NewId to avoid CacheMiss
        valid_records = self.filtered(lambda r: r.id and not str(r.id).startswith('NewId'))
        
        if not valid_records:
            # Set default value for new records
            for record in self:
                record.internal_index = ''
            return
        
        # Call original method only for valid records
        super(AccountBankStatementLine, valid_records)._compute_internal_index()
        
        # Set default value for new records
        for record in self - valid_records:
            record.internal_index = ''

    def _compute_is_reconciled(self):
        """Override to handle NewId records safely"""
        # Filter out records with NewId to avoid CacheMiss
        valid_records = self.filtered(lambda r: r.id and not str(r.id).startswith('NewId'))
        
        if not valid_records:
            # Set default values for new records
            for record in self:
                record.amount_residual = 0.0
                record.is_reconciled = False
            return
        
        # Call original method only for valid records
        super(AccountBankStatementLine, valid_records)._compute_is_reconciled()
        
        # Set default values for new records
        for record in self - valid_records:
            record.amount_residual = 0.0
            record.is_reconciled = False 