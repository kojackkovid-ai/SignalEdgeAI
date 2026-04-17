"""
Background Tasks Module
Contains scheduled tasks for emails, predictions, notifications, etc.
"""

from app.tasks.email_tasks import (
    send_daily_digest,
    send_weekly_digest,
    send_accuracy_milestone_emails,
    run_email_task_loop
)

__all__ = [
    'send_daily_digest',
    'send_weekly_digest',
    'send_accuracy_milestone_emails',
    'run_email_task_loop'
]
