# Energy Communities API

HTTP API to request information about energy communities, members and projects

## Changelog

### 2026-01-08 (v16.0.0.4.3)

- wp_coordinator_landing_page_id on landing opendata endpoint

### 2025-11-26 (v16.0.0.4.2)

- adapt `ArkenovaBacked` to renamed parameter `energy_consumption` for `energy_imported`
- fix error message when arkenova api doesn't return a json response
- fix condition to return metrics in
  `ProjectApiMetricsInfo.get_project_metrics_by_member`

### 2025-09-024 (v16.0.0.4.1)

- rename `_compute_payment_state` method to `_compute_payment_state_for_api`

### 2025-09-024 (v16.0.0.4.0)

Added invoice endpoints:

- [GET] /api/energy-communities/me/invoices
- [GET] /api/energy-communities/me/invoices/13314
- [GET] /api/energy-communities/me/invoices/13314/download

### 2025-06-03 (v16.0.0.3.1)

- `EnergyCommunityApiService.energy_community` now returns all services of an energy
  community and if is active or not for that energy community

### 2025-05-21

- Added Readme
