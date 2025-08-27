Trendz Portal (salesportal)
==========================

Lightweight README and runbook for the Trendz / Al Malika Sales Portal.

Summary
- Django-based multi-tenant sales/inventory portal used by Trendz and Al Malika sites.
- Features: invoices, customers, products, procurement, finance reports, multi-site support via Django `sites`.

Quick start (development)
1. Clone the repo and open project root (this file):
   cd /home/essyem/tp/trendzportal

2. Create & activate virtualenv:
   python3 -m venv .venv
   source .venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt

4. Apply migrations:
   python3 manage.py migrate

5. Create a superuser for admin access:
   python3 manage.py createsuperuser

6. Create Site record for Al Malika (recommended via admin):
   - Start server: python3 manage.py runserver
   - Visit http://127.0.0.1:8000/admin/sites/site/ and add Site:
     Domain: portal.almalikaqatar.com
     Name: Al Malika
   - Alternatively create via shell:
     python3 manage.py shell
     >>> from django.contrib.sites.models import Site
     >>> Site.objects.get_or_create(domain='portal.almalikaqatar.com', defaults={'name':'Al Malika'})

7. (Optional) Add host mapping for local testing:
   - Edit `/etc/hosts` (requires sudo) and add: `127.0.0.1 portal.almalikaqatar.com`

Seeder (dummy data for Al Malika)
- A management command seeds Customers, Products, Suppliers, PurchaseOrders and Invoices for the Al Malika site.
- Command: python3 manage.py create_dummy_almalika
- To explicitly target site domain: python3 manage.py create_dummy_almalika --domain=portal.almalikaqatar.com

Verification
- After running the seeder and starting the server, verify via the admin:
  http://127.0.0.1:8000/admin/
  Check: Customers, Products, Invoices, Suppliers, PurchaseOrders; ensure their `site` matches Al Malika.

Notes & troubleshooting
- If you see `ModuleNotFoundError: No module named 'django'` ensure you activated the virtualenv and installed requirements.
- If objects don't appear on the correct site, ensure the `Site` entry exists and that either request hostname matches Site.domain or `SITE_ID` in settings is set for tests.

Developer commands (useful)
- Run server: python3 manage.py runserver
- Run tests: python3 manage.py test
- Lint: (project specific)

Contact
- For more help, provide the target environment details and I can add CI/test steps or extend the seeder.
