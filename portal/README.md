Portal app README
==================

This document covers the `portal` Django app specifics and developer runbook for site setup and testing.

What this app contains
- Invoice, Customer, Product models and views
- Multi-tenant `SiteModel` base class (models have `site` FK)
- Management command `create_dummy_almalika` that seeds dummy data for Al Malika site
  - Location: `portal/management/commands/create_dummy_almalika.py`

Running the Al Malika seeder
1. Ensure project venv is active and migrations applied.
2. Make sure a Site record exists with domain `portal.almalikaqatar.com` (name: "Al Malika").
3. Run:
   python3 manage.py create_dummy_almalika --domain=portal.almalikaqatar.com

Notes for QA
- The seeder sets `site` on created objects so they are visible when the current site matches the Site record.
- If the site is not found by domain, the command falls back to Site named "Al Malika" and finally creates a Site with the provided domain.

Code pointers
- `portal/models.py` - SiteModel, Customer, Invoice, Product
- `portal/views.py` - invoice and customer CBVs; invoice create template: `templates/portal/invoice_create.html`
- `templates/portal/invoice_create.html` - Add Customer control now links to `{% url 'portal:customer_create' %}`

Extending the seeder
- If you want more control (counts, randomized dates, idempotency), I can add CLI args such as `--customers`, `--products`, `--invoices` and a `--force` flag.
