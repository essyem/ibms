from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portal'

    def ready(self):
        # Import compatibility shim early so it patches pydyf before
        # WeasyPrint is ever imported elsewhere in the app.
        try:
            from .utils import weasy_pydyf_compat  # noqa: F401
        except Exception:
            # Don't let a shim failure prevent the app from starting; the
            # error will be visible in logs when PDF generation is attempted.
            pass
