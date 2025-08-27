Missing templates summary

Scanned apps and results:
- portal: many templates (see portal.md). Only `base.html` and `index.html` overridden per-site.
- finance: two templates present; no site overrides.
- procurement: templates live under `templates/portal/` and lack site overrides.
- rbac: shared templates; no site overrides.

Next steps suggestions:
1. If you want per-site branding, scaffold site-specific stubs for the high-priority templates listed in `portal.md` and `procurement.md`.
2. Reorder middleware to ensure tenant middleware runs before authentication (I can apply the change and run tests if you want).
3. Add a small management command to list missing templates for any additional sites.

If you'd like, I can now scaffold stubs for `invoice_base.html`, `invoice_pdf.html`, `dashboard.html`, and `portal/includes/*` under both `templates/sites/portal/` and `templates/sites/almalika/`.
