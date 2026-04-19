"""
OWASP Security Best Practices Implementation
Implements OWASP Top 10 security recommendations
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class OWASPSecurityMiddleware(BaseHTTPMiddleware):
    """
    Implements OWASP security headers and validation
    Reference: https://owasp.org/www-project-secure-headers/
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # OWASP Header 1: Strict-Transport-Security (HSTS)
        # Enforces HTTPS for all future requests
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # OWASP Header 2: Content-Security-Policy (CSP)
        # Prevents XSS attacks by restricting content sources
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' fonts.gstatic.com; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        
        # OWASP Header 3: X-Content-Type-Options
        # Prevents MIME-sniffing attacks
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # OWASP Header 4: X-Frame-Options
        # Prevents clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # OWASP Header 5: X-XSS-Protection
        # Legacy XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # OWASP Header 6: Referrer-Policy
        # Controls referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # OWASP Header 7: Permissions-Policy (Feature-Policy)
        # Controls browser features and APIs
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(), "
            "camera=(), "
            "display-capture=(), "
            "document-domain=(), "
            "encrypted-media=(), "
            "fullscreen=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "midi=(), "
            "payment=(), "
            "picture-in-picture=(), "
            "sync-xhr=(), "
            "usb=(), "
            "vr=(), "
            "xr-spatial-tracking=()"
        )
        
        # OWASP Header 8: Expect-CT
        # Requires Certificate Transparency
        response.headers["Expect-CT"] = "max-age=86400, enforce"
        
        # Remove sensitive headers that might leak info
        # MutableHeaders doesn't support pop(), use del instead
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        
        return response


def setup_owasp_security(app: FastAPI):
    """
    Setup OWASP security middleware and protections
    
    Covers OWASP Top 10:
    1. Injection - Handled by Pydantic validation
    2. Broken Authentication - JWT with expiration
    3. Sensitive Data Exposure - HTTPS + encryption headers
    4. XML External Entities - Not using XML parsing
    5. Broken Access Control - Rate limiting + auth checks
    6. Security Misconfiguration - OWASP headers
    7. Cross-Site Scripting (XSS) - CSP headers
    8. Insecure Deserialization - Pydantic models
    9. Using Components with Known Vulnerabilities - Dependency scanning
    10. Insufficient Logging & Monitoring - Structured logging
    """
    
    app.add_middleware(OWASPSecurityMiddleware)
    
    logger.info("✅ OWASP security middleware configured")
    logger.info("  - HSTS (Strict-Transport-Security)")
    logger.info("  - CSP (Content-Security-Policy)")
    logger.info("  - X-Content-Type-Options: nosniff")
    logger.info("  - X-Frame-Options: DENY")
    logger.info("  - X-XSS-Protection")
    logger.info("  - Referrer-Policy")
    logger.info("  - Permissions-Policy")
    logger.info("  - Expect-CT")
    
    return app
