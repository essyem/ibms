Missing site-specific templates report for `portal`

Site overrides present:
- templates/sites/portal/base.html
- templates/sites/portal/index.html

Portal templates (defaults) that do NOT have site overrides and may need branding/customization:
- barcode_scanner.html
- base.html (note: portal/base.html exists but site override also exists)
- customer_create.html
- customer_detail.html
- customer_list.html
- dashboard.html
- enquiry.html
- export_reports.html
- home.html
- invoice_base.html
- invoice_create.html
- invoice_detail.html
- invoice_edit.html
- invoice_list.html
- invoice_pdf.html
- procurement_base.html
- procurement_dashboard.html
- products/*
- profile.html
- purchase_order_*.html
- report.html
- report_base.html
- supplier_form.html
- supplier_list.html
- terms.html

Recommendation: create site-specific stubs for at least `invoice_base.html`, `invoice_pdf.html`, `dashboard.html`, `portal/includes/_header.html`, `portal/includes/_navigation.html`, and `portal/includes/_footer.html` in `templates/sites/portal/` and `templates/sites/almalika/` to allow branding changes.
