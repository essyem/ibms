"""Small runtime shim to make WeasyPrint work with mismatched pydyf APIs.

This module avoids editing site-packages. It attempts to:
- patch `weasyprint.pdf.generate_pdf` to use a prepared pydyf.PDF instance
  if pydyf's constructor signature differs from WeasyPrint's expectations.
- ensure `pdf.version` and `pdf.identifier` are bytes so WeasyPrint's
  comparisons between bytes like b'1.4' and the value succeed.

It's intentionally defensive and limited to development use.
"""

import logging

logger = logging.getLogger(__name__)

try:
    import weasyprint.pdf as weasy_pdf
    import pydyf
except Exception:
    weasy_pdf = None
    pydyf = None


def _compat_generate_pdf(document, target, zoom, attachments, optimize_size,
                         identifier, variant, version, custom_metadata):
    """Create a pydyf.PDF instance compatible with WeasyPrint and call the
    original generate_pdf implementation.
    """
    if weasy_pdf is None or pydyf is None:
        raise RuntimeError('WeasyPrint or pydyf not available for compat wrapper')

    # Build a pydyf.PDF instance, trying no-arg first then older signature
    try:
        pdf = pydyf.PDF()
    except TypeError:
        try:
            pdf = pydyf.PDF(version or '1.7', identifier)
        except Exception:
            pdf = pydyf.PDF()

    # Normalize attributes to bytes to avoid str/bytes comparisons in weasyprint
    try:
        v = getattr(pdf, 'version', None)
        if isinstance(v, str):
            try:
                pdf.version = v.encode('utf-8')
            except Exception:
                pdf.version = b'1.7'
        elif v is None:
            pdf.version = (version or '1.7').encode('utf-8')
        elif not isinstance(v, (bytes, bytearray)):
            pdf.version = str(v).encode('utf-8')

        ident = getattr(pdf, 'identifier', None)
        if isinstance(ident, str):
            try:
                pdf.identifier = ident.encode('utf-8')
            except Exception:
                pdf.identifier = b''
        elif ident is None:
            pdf.identifier = b'' if identifier is None else (
                identifier.encode('utf-8') if isinstance(identifier, str) else str(identifier).encode('utf-8')
            )
        elif not isinstance(ident, (bytes, bytearray)):
            pdf.identifier = str(ident).encode('utf-8')
    except Exception:
        # be defensive
        pass

    # Temporarily make pydyf.PDF return our instance during PDF generation
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
                                    # to call it with only self.
                                    try:
                                        orig_init(self, *args, **kwargs)
                                    except TypeError:
                                        try:
                                            orig_init(self)
                                        except Exception:
                                            # best-effort: continue without raising here
                                            pass
                                    except Exception:
                                        # unknown error from original init: continue
                                        pass

                                    # Store any provided version/identifier and coerce to bytes
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
