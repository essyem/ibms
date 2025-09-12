from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portal'

    def ready(self):
        """Application ready hook.

        Import a compatibility shim that patches pydyf before WeasyPrint is
        imported elsewhere. Any errors are intentionally ignored so the
        application can still start; failures will surface when PDF
        generation is actually attempted.
        """
        try:
            from .utils import weasy_pydyf_compat  # noqa: F401
        except Exception:
            # Keep startup resilient; log/debug output will show any problems
            # if PDF features are used later.
            pass
        
        # Import signals to register them
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
