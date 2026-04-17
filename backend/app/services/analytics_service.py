"""
Analytics Service - Track events and generate reports
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.analytics_models import (
    AnalyticsEvent,
    ConversionFunnel,
    UserEngagementMetrics,
    CohortAnalysis,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and analyzing user behavior"""

    async def log_event(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_duration_ms: Optional[float] = None,
    ) -> None:
        """
        Log an analytics event.
        
        Common event types:
        - signup: User created an account
        - login: User logged in
        - logout: User logged out
        - prediction_view: User viewed a prediction
        - prediction_unlock: User unlocked a prediction
        - tier_upgrade: User upgraded subscription tier
        - payment_attempt: User initiated payment
        - payment_complete: Payment succeeded
        - payment_failed: Payment failed
        - props_view: User viewed player/team props
        - accuracy_dashboard_view: User viewed accuracy dashboard
        - churn: User cancelled subscription
        """
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_type=event_type,
                event_data=event_data or {},
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_duration_ms=request_duration_ms,
            )
            db.add(event)
            await db.commit()
            logger.debug(f"Logged event: {event_type} for user: {user_id}")
        except Exception as e:
            logger.error(f"Error logging event {event_type}: {e}")
            await db.rollback()

    async def get_conversion_funnel(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get overall conversion funnel metrics
        
        Returns:
        {
            'total_signups': 1000,
            'total_logins': 800,
            'first_prediction_views': 600,
            'first_tier_upgrades': 150,
            'conversion_rate_to_paid': 0.15,
            'first_purchase_average_days': 7.5,
        }
        """
        try:
            result = await db.execute(select(func.count()).select_from(ConversionFunnel))
            total_signups = result.scalar() or 0

            result = await db.execute(
                select(func.count()).select_from(ConversionFunnel).where(
                    ConversionFunnel.first_login_date != None
                )
            )
            total_logins = result.scalar() or 0

            result = await db.execute(
                select(func.count()).select_from(ConversionFunnel).where(
                    ConversionFunnel.first_prediction_view_date != None
                )
            )
            first_prediction_views = result.scalar() or 0

            result = await db.execute(
                select(func.count()).select_from(ConversionFunnel).where(
                    ConversionFunnel.first_tier_upgrade_date != None
                )
            )
            first_tier_upgrades = result.scalar() or 0

            conversion_rate = (first_tier_upgrades / total_signups) if total_signups > 0 else 0

            return {
                'total_signups': total_signups,
                'total_logins': total_logins,
                'first_prediction_views': first_prediction_views,
                'first_tier_upgrades': first_tier_upgrades,
                'conversion_rate_to_paid': round(conversion_rate, 4),
                'login_rate': round(total_logins / total_signups, 4) if total_signups > 0 else 0,
                'prediction_view_rate': round(first_prediction_views / total_signups, 4) if total_signups > 0 else 0,
            }
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            return {}

    async def get_daily_active_users(self, db: AsyncSession, days: int = 30) -> Dict[str, int]:
        """
        Get daily active user count for the past N days
        
        Returns:
        {
            '2026-03-01': 250,
            '2026-03-02': 280,
            ...
        }
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await db.execute(
                select(
                    func.date(AnalyticsEvent.created_at).label('date'),
                    func.count(func.distinct(AnalyticsEvent.user_id)).label('unique_users'),
                ).where(
                    AnalyticsEvent.created_at > cutoff_date,
                    AnalyticsEvent.user_id != None,
                ).group_by(func.date(AnalyticsEvent.created_at))
                .order_by(func.date(AnalyticsEvent.created_at))
            )

            daily_users = {}
            for row in result:
                daily_users[str(row.date)] = row.unique_users

            return daily_users
        except Exception as e:
            logger.error(f"Error getting daily active users: {e}")
            return {}

    async def get_event_analytics(self, db: AsyncSession, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics on event distribution
        
        Returns:
        {
            'total_events': 10000,
            'events_by_type': {
                'prediction_view': 5000,
                'login': 3000,
                'tier_upgrade': 100,
                ...
            },
            'average_request_duration_ms': 150,
        }
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await db.execute(
                select(func.count()).select_from(AnalyticsEvent).where(
                    AnalyticsEvent.created_at > cutoff_date
                )
            )
            total_events = result.scalar() or 0

            result = await db.execute(
                select(
                    AnalyticsEvent.event_type,
                    func.count().label('count'),
                ).where(
                    AnalyticsEvent.created_at > cutoff_date
                ).group_by(AnalyticsEvent.event_type)
                .order_by(func.count().desc())
            )

            events_by_type = {}
            for row in result:
                events_by_type[row.event_type] = row.count

            result = await db.execute(
                select(func.avg(AnalyticsEvent.request_duration_ms)).select_from(
                    AnalyticsEvent
                ).where(
                    AnalyticsEvent.created_at > cutoff_date,
                    AnalyticsEvent.request_duration_ms != None,
                )
            )
            avg_request_duration = result.scalar() or 0

            return {
                'total_events': total_events,
                'events_by_type': events_by_type,
                'average_request_duration_ms': round(avg_request_duration, 2),
                'period_days': days,
            }
        except Exception as e:
            logger.error(f"Error getting event analytics: {e}")
            return {}

    async def get_churn_analysis(self, db: AsyncSession, days: int = 90) -> Dict[str, Any]:
        """
        Get user churn metrics
        
        Returns:
        {
            'total_users': 1000,
            'churned_users': 50,
            'churn_rate': 0.05,
            'avg_lifetime_days': 45,
        }
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await db.execute(
                select(func.count()).select_from(ConversionFunnel).where(
                    ConversionFunnel.signup_date > cutoff_date
                )
            )
            total_users = result.scalar() or 0

            result = await db.execute(
                select(func.count()).select_from(ConversionFunnel).where(
                    ConversionFunnel.churn_date != None,
                    ConversionFunnel.signup_date > cutoff_date,
                )
            )
            churned_users = result.scalar() or 0

            churn_rate = (churned_users / total_users) if total_users > 0 else 0

            return {
                'total_users': total_users,
                'churned_users': churned_users,
                'churn_rate': round(churn_rate, 4),
                'active_users': total_users - churned_users,
                'retention_rate': round(1 - churn_rate, 4),
                'analysis_period_days': days,
            }
        except Exception as e:
            logger.error(f"Error getting churn analysis: {e}")
            return {}

    async def get_revenue_metrics(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get revenue and monetary metrics
        
        Returns:
        {
            'mrr': 5000,  # Monthly Recurring Revenue
            'arpu': 25,   # Average Revenue Per User
            'ltv': 150,   # Lifetime Value
            'tier_breakdown': {
                'free': 700,
                'basic': 200,
                'pro': 80,
                'elite': 20,
            }
        }
        """
        try:
            result = await db.execute(
                select(func.sum(ConversionFunnel.current_subscription_value)).select_from(
                    ConversionFunnel
                ).where(ConversionFunnel.current_tier != 'free')
            )
            mrr = result.scalar() or 0

            result = await db.execute(
                select(func.count()).select_from(ConversionFunnel).where(
                    ConversionFunnel.first_tier_upgrade_date != None
                )
            )
            paid_users = result.scalar() or 0

            arpu = (mrr / paid_users) if paid_users > 0 else 0

            result = await db.execute(
                select(
                    ConversionFunnel.current_tier,
                    func.count().label('count'),
                ).group_by(ConversionFunnel.current_tier)
            )

            tier_breakdown = {}
            for row in result:
                tier_breakdown[row.current_tier or 'unknown'] = row.count

            return {
                'mrr': round(mrr, 2),
                'arpu': round(arpu, 2),
                'paid_users': paid_users,
                'tier_breakdown': tier_breakdown,
            }
        except Exception as e:
            logger.error(f"Error getting revenue metrics: {e}")
            return {}
