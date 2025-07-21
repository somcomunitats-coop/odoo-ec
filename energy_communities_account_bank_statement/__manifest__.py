{
    'name': 'Energy Communities Account Bank Statement',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Fix CacheMiss error in account.bank.statement.line',
    'description': """
        This module fixes the CacheMiss error that occurs when editing
        account.bank.statement.line records, specifically with the
        running_balance field computation.
        
        The error occurs because the running_balance field is computed
        on records with temporary IDs (NewId) that don't exist in the
        database yet.
    """,
    'author': 'Coopdevs Treball SCCL & Som Energia SCCL & SomIT',
    'website': 'https://git.coopdevs.org/coopdevs/comunitats-energetiques/odoo-ce',
    'depends': ['account'],
    'data': [
        'views/account_bank_statement_line_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
} 