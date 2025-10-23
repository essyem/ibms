"""Small runtime shim to make WeasyPrint work with mismatched pydyf APIs.

This module patches `pydyf.PDF.__init__` defensively so that callers
like WeasyPrint which call `pydyf.PDF(version, identifier)` won't raise
TypeError if the installed pydyf's constructor signature differs.

It also coerces `version` and `identifier` values to bytes because
WeasyPrint performs byte-wise comparisons (e.g. `pdf.version <= b'1.4'`).

This is a development-time compatibility shim. Prefer pinning matching
package versions for a long-term solution.
"""
import logging

logger = logging.getLogger(__name__)

try:
    import pydyf
except Exception:
    pydyf = None


def _coerce_to_bytes(value, default=b''):
    """Coerce value to bytes for WeasyPrint compatibility."""
    try:
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
        if isinstance(value, str):
            return value.encode('utf-8')
        if value is None:
            return default
        return str(value).encode('utf-8')
    except Exception:
        return default


if pydyf is not None:
    try:
        orig_init = getattr(pydyf.PDF, '__init__', None)
        if orig_init is not None:
            def _new_init(self, *args, **kwargs):
                # First, try to call the original init with the provided args.
                # If that yields a TypeError (signature mismatch), fall back to
                # calling it with only self.
                try:
                    orig_init(self, *args, **kwargs)
                except TypeError:
                    try:
                        orig_init(self)
                    except Exception:
                        # Best-effort: swallow and continue
                        pass
                except Exception:
                    # Other errors from original init should not stop us here.
                    pass

                # Store version/identifier passed by callers and coerce to bytes
                try:
                    if len(args) >= 1:
                        self.version = _coerce_to_bytes(args[0], default=b'1.7')
                    else:
                        if not hasattr(self, 'version'):
                            self.version = b'1.7'

                    if len(args) >= 2:
                        self.identifier = _coerce_to_bytes(args[1], default=b'')
                    else:
                        if not hasattr(self, 'identifier'):
                            self.identifier = b''
                except Exception:
                    # Ensure attributes exist as a last resort
                    try:
                        if not hasattr(self, 'version'):
                            self.version = b'1.7'
                        if not hasattr(self, 'identifier'):
                            self.identifier = b''
                    except Exception:
                        pass

            pydyf.PDF.__init__ = _new_init
            logger.info('Patched pydyf.PDF.__init__ to accept extra (version, identifier) args')
    except Exception:
        logger.exception('Failed to install pydyf compatibility shim')
