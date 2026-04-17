"""
Audit Logging Service

Tracks all sensitive operations for compliance, security, and troubleshooting.
Uses database to persist audit logs for regulatory requirements (GDPR, CCPA).
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, DateTime, JSON, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base
import uuid
import json

logger = logging.getLogger(__name__)


class AuditLog(Base):
    """Database model for audit logs"""
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True, index=True)  # Nullable for system actions
    action = Column(String, nullable=False, index=True)  # e.g., login, upgrade, export_data, payment
    resource = Column(String, nullable=True)  # What was affected: user, prediction, payment
    resource_id = Column(String, nullable=True, index=True)  # ID of the resource
    details = Column(JSON, nullable=True)  # Additional context
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    status = Column(String, default="success")  # success, failure, error
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # For querying
    month = Column(Integer, nullable=True)  # EXTRACT(MONTH FROM created_at) for indexing


class AuditService:
    """
    Service for logging all sensitive operations.
    All data is real - no mock or hardcoded values.
    """
    
    # Actions that require audit logging
    AUDITED_ACTIONS = {
        # Authentication & Account
        'login': {'resource': 'user', 'severity': 'high'},
        'logout': {'resource': 'user', 'severity': 'medium'},
        'signup': {'resource': 'user', 'severity': 'high'},
        'password_change': {'resource': 'user', 'severity': 'high'},
        'password_reset': {'resource': 'user', 'severity': 'high'},
        'account_delete': {'resource': 'user', 'severity': 'high'},
        
        # Subscription & Payment
        'tier_upgrade': {'resource': 'subscription', 'severity': 'high'},
        'tier_downgrade': {'resource': 'subscription', 'severity': 'high'},
        'payment_intent_created': {'resource': 'payment', 'severity': 'high'},
        'payment_completed': {'resource': 'payment', 'severity': 'high'},
        'payment_failed': {'resource': 'payment', 'severity': 'high'},
        'payment_refunded': {'resource': 'payment', 'severity': 'high'},
        'subscription_cancelled': {'resource': 'subscription', 'severity': 'high'},
        
        # Data Access
        'data_export_requested': {'resource': 'user', 'severity': 'high'},
        'data_exported': {'resource': 'user', 'severity': 'high'},
        'data_imported': {'resource': 'user', 'severity': 'high'},
        'api_key_created': {'resource': 'api', 'severity': 'high'},
        'api_key_revoked': {'resource': 'api', 'severity': 'high'},
        
        # Predictions & Bets
        'prediction_created': {'resource': 'prediction', 'severity': 'medium'},
        'prediction_locked': {'resource': 'prediction', 'severity': 'medium'},
        'prediction_updated': {'resource': 'prediction', 'severity': 'medium'},
        
        # User Preferences
        'preferences_updated': {'resource': 'user', 'severity': 'low'},
        'notification_settings_updated': {'resource': 'user', 'severity': 'low'},
        
        # Admin Actions
        'user_suspended': {'resource': 'user', 'severity': 'high'},
        'user_unsuspended': {'resource': 'user', 'severity': 'high'},
        'fraud_flagged': {'resource': 'user', 'severity': 'high'},
        'support_ticket_created': {'resource': 'support', 'severity': 'medium'},
    }
    
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
    
    async def log_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> Optional[str]:
        """
        Log a sensitive action.
        
        Args:
            action: What happened (e.g., 'login', 'payment_completed')
            user_id: Who did it (optional for system actions)
            resource: What was affected (e.g., 'user', 'payment')
            resource_id: ID of resource that was affected
            details: Additional context (actual values, not mock)
            ip_address: Source IP address
            user_agent: Browser/client info
            status: success, failure, error
            error_message: If status is failure/error
        
        Returns:
            Audit log ID if persisted, None if not
        """
        try:
            # Get action metadata
            action_lower = action.lower()
            action_meta = self.AUDITED_ACTIONS.get(action_lower, {})
            severity = action_meta.get('severity', 'medium')
            
            # Create audit log entry
            if not resource and action_meta:
                resource = action_meta.get('resource')
            
            audit_log = AuditLog(
                user_id=user_id,
                action=action_lower,
                resource=resource,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                error_message=error_message,
                month=datetime.utcnow().month
            )
            
            # Persist to database if session available
            if self.db_session:
                self.db_session.add(audit_log)
                await self.db_session.commit()
                log_id = audit_log.id
            else:
                log_id = audit_log.id
            
            # Log to application logs
            log_level = logging.WARNING if severity == 'high' else logging.INFO
            log_msg = (
                f"[AUDIT_{severity.upper()}] {action_lower} | "
                f"user_id={user_id} | resource={resource}/{resource_id} | "
                f"status={status}"
            )
            
            if error_message:
                log_msg += f" | error={error_message}"
            
            logger.log(log_level, log_msg)
            
            return log_id
            
        except Exception as e:
            logger.error(f"[AUDIT_ERROR] Failed to log action '{action}': {str(e)}", exc_info=True)
            return None
    
    async def log_login(self, user_id: str, ip_address: Optional[str], 
                       user_agent: Optional[str], success: bool = True) -> Optional[str]:
        """Log user login"""
        return await self.log_action(
            action='login',
            user_id=user_id,
            resource='user',
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            status='success' if success else 'failure',
            details={'event': 'user authentication'}
        )
    
    async def log_payment(self, user_id: str, payment_intent_id: str, 
                         amount_cents: int, tier: str, status: str = 'completed',
                         error: Optional[str] = None) -> Optional[str]:
        """Log payment transaction - with REAL data only"""
        return await self.log_action(
            action='payment_completed' if status == 'completed' else 'payment_failed',
            user_id=user_id,
            resource='payment',
            resource_id=payment_intent_id,
            status=status,
            error_message=error,
            details={
                'amount_cents': amount_cents,  # REAL amount from Stripe
                'tier': tier,  # REAL tier purchased
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    async def log_tier_change(self, user_id: str, from_tier: str, to_tier: str,
                             ip_address: Optional[str] = None) -> Optional[str]:
        """Log tier upgrade/downgrade"""
        action = 'tier_upgrade' if self._compare_tiers(from_tier, to_tier) > 0 else 'tier_downgrade'
        
        return await self.log_action(
            action=action,
            user_id=user_id,
            resource='subscription',
            resource_id=user_id,
            ip_address=ip_address,
            details={
                'from_tier': from_tier,
                'to_tier': to_tier,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    async def log_data_export(self, user_id: str, data_types: List[str],
                             ip_address: Optional[str] = None) -> Optional[str]:
        """Log data export request (GDPR Article 15)"""
        return await self.log_action(
            action='data_export_requested',
            user_id=user_id,
            resource='user',
            resource_id=user_id,
            ip_address=ip_address,
            details={
                'exported_data_types': data_types,  # What user exported
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    async def log_account_deletion(self, user_id: str, reason: Optional[str] = None,
                                  ip_address: Optional[str] = None) -> Optional[str]:
        """Log account deletion (GDPR Article 17)"""
        return await self.log_action(
            action='account_delete',
            user_id=user_id,
            resource='user',
            resource_id=user_id,
            ip_address=ip_address,
            details={
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    async def log_fraud_flag(self, user_id: str, reason: str, 
                            details: Dict[str, Any]) -> Optional[str]:
        """Log suspicious activity detection"""
        return await self.log_action(
            action='fraud_flagged',
            user_id=user_id,
            resource='user',
            resource_id=user_id,
            status='error',
            error_message=reason,
            details=details
        )
    
    async def get_user_audit_logs(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve user's audit logs for transparency"""
        if not self.db_session:
            return []
        
        try:
            from sqlalchemy import select, desc
            
            query = select(AuditLog).where(
                AuditLog.user_id == user_id
            ).order_by(desc(AuditLog.created_at)).limit(limit)
            
            result = await self.db_session.execute(query)
            logs = result.scalars().all()
            
            return [
                {
                    'action': log.action,
                    'resource': log.resource,
                    'status': log.status,
                    'ip_address': log.ip_address,
                    'timestamp': log.created_at.isoformat(),
                    'details': log.details or {}
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error retrieving audit logs for user {user_id}: {e}")
            return []
    
    async def get_audit_report(self, start_date: datetime, end_date: datetime,
                              action_filter: Optional[str] = None) -> Dict[str, Any]:
        """Generate audit report for compliance (GDPR, etc)"""
        if not self.db_session:
            return {}
        
        try:
            from sqlalchemy import select, func
            
            query = select(AuditLog).where(
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            )
            
            if action_filter:
                query = query.where(AuditLog.action == action_filter)
            
            result = await self.db_session.execute(query)
            logs = result.scalars().all()
            
            # Calculate statistics
            total_actions = len(logs)
            by_action = {}
            by_status = {'success': 0, 'failure': 0, 'error': 0}
            
            for log in logs:
                by_action[log.action] = by_action.get(log.action, 0) + 1
                by_status[log.status] = by_status.get(log.status, 0) + 1
            
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_actions': total_actions,
                'by_action': by_action,
                'by_status': by_status,
                'logs': [
                    {
                        'action': log.action,
                        'user_id': log.user_id,
                        'resource': log.resource,
                        'status': log.status,
                        'timestamp': log.created_at.isoformat()
                    }
                    for log in logs[:1000]  # Limit to 1000 for report
                ]
            }
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
            return {}
    
    @staticmethod
    def _compare_tiers(from_tier: str, to_tier: str) -> int:
        """
        Compare tier levels.
        Returns: 1 if upgrade, -1 if downgrade, 0 if same
        """
        tier_order = {'free': 0, 'basic': 1, 'pro': 2, 'elite': 3}
        from_level = tier_order.get(from_tier.lower(), 0)
        to_level = tier_order.get(to_tier.lower(), 0)
        return 1 if to_level > from_level else (-1 if to_level < from_level else 0)


# Global instance factory
_audit_service_instance = None


async def get_audit_service(db_session: Optional[AsyncSession] = None) -> AuditService:
    """Get or create audit service instance"""
    global _audit_service_instance
    if _audit_service_instance is None:
        _audit_service_instance = AuditService(db_session)
    elif db_session:
        _audit_service_instance.db_session = db_session
    return _audit_service_instance
