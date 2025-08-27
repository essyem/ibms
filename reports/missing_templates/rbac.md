Missing site-specific templates report for `rbac`

RBAC templates present:
- templates/rbac/register.html
- templates/rbac/emails/ (email templates)

No site-specific overrides found. RBAC UI typically is shared, but if you need different registration flows or role displays per site, create `templates/sites/portal/rbac/` and `templates/sites/almalika/rbac/`.

Recommendation: keep RBAC shared where possible; only override per-site when role sets or registration wording differ.
