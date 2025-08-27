# Missing template overrides by app

This report lists template files under `templates/` that do not have site-specific overrides under `templates/sites/<site>/` for the existing sites `portal` and `almalika`.

Summary:

- portal: many templates under `templates/portal/` do not have site-specific overrides (invoice_base, invoice_pdf, dashboard, includes/_header.html, includes/_navigation.html, includes/_footer.html, etc.).
- finance: templates live under `templates/portal/` and lack site overrides.
- procurement: templates under `templates/portal/` (purchase_order_*, procurement_base) lack site overrides.
- rbac: no site-specific overrides found.

Recommendations:

1. Create site-specific stubs under `templates/sites/<site>/` for templates that require branding changes. Typical candidates: `invoice_pdf.html`, `invoice_base.html`, `dashboard.html`, and header/navigation/footer includes.
2. Use the global `templates/includes/_navigation.html` as the canonical navigation implementation and create minimal site wrappers that include it (already done for `portal` and `almalika`).
3. Keep the site wrappers minimal so updates to behavior (JS toggle) are applied globally.

If you'd like, I can scaffold more stubs for each missing template under both `portal` and `almalika` now.
