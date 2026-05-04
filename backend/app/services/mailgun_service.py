"""
Deprecated Mailgun compatibility shim
This module re-exports SendGridService for backwards compatibility.
"""

from app.services.sendgrid_service import SendGridService

__all__ = ["SendGridService"]
