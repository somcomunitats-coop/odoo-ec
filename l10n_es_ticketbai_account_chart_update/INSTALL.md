# Installation and Testing Guide

## Problem Description

When updating fiscal positions using the `account_chart_update` wizard with the
`l10n_es_ticketbai` module installed, a `ValueError` is raised:

```
ValueError: Wrong value for account.fiscal.position.tbai_vat_exemption_ids: account.fp.tbai.tax_template(1,)
```

This occurs because the wizard doesn't know how to convert TicketBAI fiscal position
template fields (`account.fp.tbai.tax_template`) to real records
(`account.fp.tbai.tax`).

## Solution

This integration module extends the `account_chart_update` wizard to properly handle
TicketBAI fiscal position fields during chart of accounts updates.

## Installation

1. Ensure both dependencies are installed:

   - `l10n_es_ticketbai`
   - `account_chart_update`

2. Install this module:

   ```bash
   # From Odoo interface: Apps > Update Apps List
   # Then search for "TicketBAI - Account Chart Update Integration"
   # Click Install
   ```

3. The module is set to auto_install=True, so it will be automatically installed when
   both dependencies are present.

## Testing

### Manual Testing

1. Create or update a company with Spanish chart of accounts
2. Install `l10n_es_ticketbai` module
3. Go to Accounting > Configuration > Update Chart of Accounts
4. Select the company and chart template
5. Click "Find Records to Update"
6. Select fiscal positions to update
7. Click "Update Records"

The update should complete successfully without the ValueError.

### Unit Testing

Run tests using the Odoo test framework:

```bash
# From Docker container
docker-compose -f devel.yaml run --rm odoo \
  --test-enable \
  --test-tags /l10n_es_ticketbai_account_chart_update \
  --stop-after-init \
  -i l10n_es_ticketbai_account_chart_update
```

Or from within the container:

```bash
odoo --test-enable \
  --test-tags /l10n_es_ticketbai_account_chart_update \
  --stop-after-init \
  -i l10n_es_ticketbai_account_chart_update \
  -d test_db
```

## Technical Details

The module extends three methods in `wizard.update.charts.accounts`:

1. **`find_fp_tbai_tax_by_templates`**: Converts template exemptions to real records
2. **`diff_fields`**: Detects differences in TicketBAI fields between templates and real
   records
3. **`_prepare_fp_vals`**: Includes TicketBAI exemptions when creating new fiscal
   positions

These extensions ensure that TicketBAI fiscal position fields are properly synchronized
during chart of accounts updates.
