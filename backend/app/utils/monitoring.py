"""
Monitoring, metrics, and alerting service
Tracks application health, performance, and errors
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Alert notification"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class PerformanceMetrics:
    """Track application performance metrics"""
    
    def __init__(self, window_size: int = 1000):
        """
        Args:
            window_size: Number of requests to keep in memory
        """
        self.window_size = window_size
        self.requests: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
    
    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: Optional[str] = None
    ):
        """Record API request metrics"""
        self.requests.append({
            "timestamp": datetime.utcnow(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
            "user_id": user_id,
        })
        
        # Keep window size limited
        if len(self.requests) > self.window_size:
            self.requests = self.requests[-self.window_size:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.requests:
            return {}
        
        response_times = [r["response_time"] for r in self.requests]
        status_codes = defaultdict(int)
        paths = defaultdict(int)
        
        for r in self.requests:
            status_codes[r["status_code"]] += 1
            paths[r["path"]] += 1
        
        return {
            "total_requests": len(self.requests),
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            "p99_response_time": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
            "status_codes": dict(status_codes),
            "top_paths": dict(sorted(paths.items(), key=lambda x: x[1], reverse=True)[:10]),
            "error_rate": sum(1 for r in self.requests if r["status_code"] >= 400) / len(self.requests)
        }


class ErrorMetrics:
    """Track application errors"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.errors: List[Dict[str, Any]] = []
        self.error_count = defaultdict(int)
    
    def record_error(
        self,
        error_code: str,
        message: str,
        status_code: int,
        path: str,
        exception: Optional[Exception] = None
    ):
        """Record error occurrence"""
        self.errors.append({
            "timestamp": datetime.utcnow(),
            "error_code": error_code,
            "message": message,
            "status_code": status_code,
            "path": path,
            "exception_type": type(exception).__name__ if exception else None,
        })
        
        self.error_count[error_code] += 1
        
        # Keep window limited
        if len(self.errors) > self.window_size:
            self.errors = self.errors[-self.window_size:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        if not self.errors:
            return {"total_errors": 0, "error_breakdown": {}}
        
        return {
            "total_errors": len(self.errors),
            "error_breakdown": dict(self.error_count),
            "recent_errors": self.errors[-10:],
        }


class ModelMetrics:
    """Track ML model performance"""
    
    def __init__(self):
        self.predictions_made = 0
        self.predictions_correct = 0
        self.confidence_scores = []
        self.accuracy_history: List[Dict] = []
    
    def record_prediction(
        self,
        prediction_id: str,
        confidence: float,
        model_name: str,
        sport: str
    ):
        """Record ML prediction"""
        self.predictions_made += 1
        self.confidence_scores.append(confidence)
    
    def record_resolution(
        self,
        prediction_id: str,
        result: str,
        correct: bool
    ):
        """Record prediction outcome"""
        if correct:
            self.predictions_correct += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        if self.predictions_made == 0:
            return {"accuracy": 0}
        
        avg_confidence = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0
        
        return {
            "predictions_made": self.predictions_made,
            "predictions_correct": self.predictions_correct,
            "accuracy": self.predictions_correct / self.predictions_made,
            "avg_confidence": avg_confidence,
            "confidence_distribution": {
                "high": sum(1 for c in self.confidence_scores if c > 0.7),
                "medium": sum(1 for c in self.confidence_scores if 0.4 <= c <= 0.7),
                "low": sum(1 for c in self.confidence_scores if c < 0.4),
            }
        }


class HealthChecker:
    """Check application health status"""
    
    def __init__(self):
        self.health_checks: Dict[str, Dict] = {}
    
    def register_check(
        self,
        name: str,
        check_fn,
        interval: int = 60
    ):
        """Register a health check"""
        self.health_checks[name] = {
            "fn": check_fn,
            "interval": interval,
            "last_check": None,
            "status": "unknown",
            "message": "",
        }
    
    async def run_check(self, name: str) -> bool:
        """Run a single health check"""
        if name not in self.health_checks:
            return False
        
        check = self.health_checks[name]
        try:
            result = await check["fn"]() if asyncio.iscoroutinefunction(check["fn"]) else check["fn"]()
            check["status"] = "healthy" if result else "unhealthy"
            check["last_check"] = datetime.utcnow()
            return result
        except Exception as e:
            check["status"] = "error"
            check["message"] = str(e)
            check["last_check"] = datetime.utcnow()
            return False
    
    async def run_all_checks(self) -> Dict[str, bool]:
        """Run all health checks"""
        results = {}
        for name in self.health_checks:
            results[name] = await self.run_check(name)
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        all_healthy = all(
            check["status"] == "healthy"
            for check in self.health_checks.values()
        )
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                name: {
                    "status": check["status"],
                    "last_check": check["last_check"].isoformat() if check["last_check"] else None,
                    "message": check["message"],
                }
                for name, check in self.health_checks.items()
            }
        }


class AlertManager:
    """Manage system alerts"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_thresholds = {
            "error_rate": 0.05,  # Alert if >5% errors
            "response_time": 1000,  # Alert if avg response > 1s
            "accuracy": 0.50,  # Alert if accuracy < 50%
            "uptime": 0.99,  # Alert if uptime < 99%
        }
    
    def create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str
    ) -> Alert:
        """Create a new alert"""
        alert = Alert(
            id=f"alert_{datetime.utcnow().timestamp()}",
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
        )
        self.alerts.append(alert)
        
        # Log based on severity
        log_fn = {
            AlertSeverity.INFO: logger.info,
            AlertSeverity.WARNING: logger.warning,
            AlertSeverity.ERROR: logger.error,
            AlertSeverity.CRITICAL: logger.critical,
        }.get(severity, logger.warning)
        
        log_fn(f"[{severity.value}] {title}: {message}")
        
        return alert
    
    def check_thresholds(self, metrics: Dict[str, Any]):
        """Check if metrics exceed thresholds and create alerts"""
        
        # Check error rate
        if metrics.get("error_rate", 0) > self.alert_thresholds["error_rate"]:
            self.create_alert(
                AlertSeverity.WARNING,
                "High Error Rate",
                f"Error rate is {metrics['error_rate']:.2%}, threshold is {self.alert_thresholds['error_rate']:.2%}"
            )
        
        # Check response time
        if metrics.get("avg_response_time", 0) > self.alert_thresholds["response_time"]:
            self.create_alert(
                AlertSeverity.WARNING,
                "Slow Response Times",
                f"Average response time is {metrics['avg_response_time']:.0f}ms, threshold is {self.alert_thresholds['response_time']}ms"
            )
        
        # Check model accuracy
        if metrics.get("accuracy", 1) < self.alert_thresholds["accuracy"]:
            self.create_alert(
                AlertSeverity.ERROR,
                "Low Model Accuracy",
                f"Model accuracy is {metrics['accuracy']:.2%}, threshold is {self.alert_thresholds['accuracy']:.2%}"
            )
    
    def resolve_alert(self, alert_id: str):
        """Mark alert as resolved"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts"""
        return [a for a in self.alerts if not a.resolved]


class MonitoringService:
    """Main monitoring service combining all metrics"""
    
    def __init__(self):
        self.performance = PerformanceMetrics()
        self.errors = ErrorMetrics()
        self.models = ModelMetrics()
        self.health = HealthChecker()
        self.alerts = AlertManager()
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all metrics for monitoring dashboard"""
        
        perf_stats = self.performance.get_stats()
        error_stats = self.errors.get_stats()
        model_stats = self.models.get_stats()
        health_status = self.health.get_status()
        active_alerts = [
            {
                "id": a.id,
                "severity": a.severity.value,
                "title": a.title,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in self.alerts.get_active_alerts()
        ]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": perf_stats,
            "errors": error_stats,
            "models": model_stats,
            "health": health_status,
            "alerts": active_alerts,
        }


# Global monitoring service instance
_monitoring: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get or create global monitoring service"""
    global _monitoring
    if not _monitoring:
        _monitoring = MonitoringService()
    return _monitoring


def init_monitoring() -> MonitoringService:
    """Initialize monitoring service with default health checks"""
    monitoring = get_monitoring_service()
    
    # Register default health checks
    async def check_database():
        # TODO: Implement actual database health check
        return True
    
    async def check_redis():
        # TODO: Implement actual redis health check
        return True
    
    async def check_ml_models():
        # TODO: Implement ML model health check
        return True
    
    monitoring.health.register_check("database", check_database)
    monitoring.health.register_check("redis", check_redis)
    monitoring.health.register_check("ml_models", check_ml_models)
    
    return monitoring
