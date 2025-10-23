Missing site-specific templates report for `procurement`

There is no `templates/procurement/` in the repository root. Procurement templates appear under `templates/portal/` (procurement_base.html, procurement_dashboard.html, supplier_form/list, purchase_order_*) and none of these have site-specific overrides.

Recommendation: if procurement needs site-specific layouts, create `templates/sites/portal/procurement/` and `templates/sites/almalika/procurement/` and add stubs for:
- procurement_base.html
- procurement_dashboard.html
- supplier_form.html
- supplier_list.html
- purchase_order_form.html
- purchase_order_list.html
- purchase_order_detail.html

