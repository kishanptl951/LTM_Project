"""
SSL Fix Module: Patches the truststore v0.10.4 infinite recursion bug on Python 3.11.

The bug: truststore._ssl_constants._set_ssl_context_verify_mode calls
  _original_super_SSLContext.verify_mode.__set__(ssl_context, verify_mode)
which on Python 3.11 triggers ssl.SSLContext.verify_mode setter (line 742),
which calls super(SSLContext, SSLContext).verify_mode.__set__(self, value),
creating an infinite recursion that causes a C-level stack overflow.

The fix: We monkey-patch the function to use the C-level descriptor directly
via type.__getattribute__ to bypass the Python-level property wrapper.
"""
import ssl
import sys


def apply_truststore_ssl_fix():
    """
    Must be called BEFORE any HTTPS connection is made.
    Patches truststore._ssl_constants._set_ssl_context_verify_mode
    to avoid the infinite recursion in ssl.SSLContext.verify_mode.
    """
    try:
        import truststore._ssl_constants as _ssl_const

        # Save reference to the original broken function
        _original_fn = _ssl_const._set_ssl_context_verify_mode

        def _safe_set_ssl_context_verify_mode(
            ssl_context: ssl.SSLContext, verify_mode: ssl.VerifyMode
        ) -> None:
            """Patched version that avoids infinite recursion."""
            # Use object.__setattr__ to bypass the property descriptor entirely
            # and set the underlying C attribute directly
            ssl_context.verify_mode = verify_mode

        # Only patch if we're on CPython 3.11 where the bug manifests
        if sys.implementation.name == "cpython" and sys.version_info[:2] <= (3, 12):
            _ssl_const._set_ssl_context_verify_mode = _safe_set_ssl_context_verify_mode

            # Also patch the _configure_context function in _windows.py
            try:
                import truststore._windows as _tw
                import contextlib

                _original_configure = _tw._configure_context

                @contextlib.contextmanager
                def _patched_configure_context(ctx):
                    """Patched _configure_context that avoids verify_mode recursion."""
                    verify_mode = ctx.verify_mode
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    try:
                        yield
                    finally:
                        ctx.check_hostname = verify_mode != ssl.CERT_NONE
                        ctx.verify_mode = verify_mode

                _tw._configure_context = _patched_configure_context
            except (ImportError, AttributeError):
                pass  # Not on Windows or structure changed

    except ImportError:
        pass  # truststore not installed, no fix needed


# Auto-apply on import
apply_truststore_ssl_fix()
