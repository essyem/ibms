Missing site-specific templates report for `finance`

Site overrides present:
- templates/sites/portal/base.html
- templates/sites/almalika/base.html

Finance templates in `templates/finance/`:
- dashboard.html
- transaction_form.html

Neither of these has site-specific overrides. If finance UI needs per-site branding or different summaries, create copies under `templates/sites/portal/finance/` and `templates/sites/almalika/finance/`.

Recommendation: add `finance/dashboard.html` stub under site folders if the financial dashboard differs between sites.
