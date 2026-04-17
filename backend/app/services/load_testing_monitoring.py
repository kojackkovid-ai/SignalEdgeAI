"""
Load Testing and Monitoring Tools
Tests platform performance and monitors for issues
"""

import time
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
import os

logger = logging.getLogger(__name__)

# ============================================================================
# LOAD TESTING
# ============================================================================

class LoadTestRunner:
    """Run load tests against API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.errors = []
    
    async def run_prediction_Load_test(
        self,
        num_users: int = 100,
        requests_per_user: int = 10,
        ramp_up_seconds: int = 60
    ) -> Dict:
        """
        Simulate multiple users making prediction requests
        
        Metrics collected:
        - Response times
        - Error rates
        - Throughput
        """
        start_time = time.time()
        
        logger.info(f"Starting load test: {num_users} users, {requests_per_user} req/user")
        
        # Create tasks for each user
        tasks = []
        for user_id in range(num_users):
            delay = (user_id / num_users) * ramp_up_seconds
            task = asyncio.create_task(
                self._user_session(user_id, requests_per_user, delay)
            )
            tasks.append(task)
        
        # Wait for all to complete
        await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Calculate statistics
        report = self._analyze_results(elapsed, num_users, requests_per_user)
        
        return report
    
    async def _user_session(self, user_id: int, num_requests: int, initial_delay: float):
        """Simulate one user making multiple requests"""
        await asyncio.sleep(initial_delay)
        
        for request_num in range(num_requests):
            try:
                # Simulate API call
                start = time.time()
                
                # Mock endpoint: GET /api/predictions/nba
                response_time = await self._make_request()
                
                elapsed = time.time() - start
                
                self.results.append({
                    'user_id': user_id,
                    'request_num': request_num,
                    'response_time': elapsed,
                    'timestamp': datetime.utcnow()
                })
                
                # Small delay between requests
                await asyncio.sleep(0.5)
            
            except Exception as e:
                self.errors.append({
                    'user_id': user_id,
                    'error': str(e),
                    'timestamp': datetime.utcnow()
                })
    
    async def _make_request(self) -> float:
        """Simulate making HTTP request"""
        # In production, would use httpx.AsyncClient()
        # For now, simulate with random delay
        import random
        delay = random.uniform(0.1, 0.5)
        await asyncio.sleep(delay)
        return delay
    
    def _analyze_results(self, elapsed_time: float, users: int, req_per_user: int) -> Dict:
        """Analyze load test results"""
        total_requests = len(self.results)
        error_count = len(self.errors)
        
        if not self.results:
            return {'status': 'no_data'}
        
        response_times = [r['response_time'] for r in self.results]
        
        import numpy as np
        
        return {
            'summary': {
                'total_time_seconds': elapsed_time,
                'total_requests': total_requests,
                'total_errors': error_count,
                'error_rate': error_count / total_requests if total_requests > 0 else 0,
                'throughput_rps': total_requests / elapsed_time
            },
            'response_time_stats': {
                'min_ms': min(response_times) * 1000,
                'max_ms': max(response_times) * 1000,
                'mean_ms': np.mean(response_times) * 1000,
                'median_ms': np.median(response_times) * 1000,
                'p95_ms': np.percentile(response_times, 95) * 1000,
                'p99_ms': np.percentile(response_times, 99) * 1000,
                'stdev_ms': np.std(response_times) * 1000
            },
            'conclusions': self._generate_conclusions(response_times, error_count, total_requests)
        }
    
    def _generate_conclusions(
        self,
        response_times: List[float],
        error_count: int,
        total_requests: int
    ) -> List[str]:
        """Generate human-readable conclusions"""
        import numpy as np
        conclusions = []
        
        p95 = np.percentile(response_times, 95)
        p99 = np.percentile(response_times, 99)
        mean = np.mean(response_times)
        
        # Check response times
        if p95 < 0.5:
            conclusions.append("✓ Excellent response times (P95 < 500ms)")
        elif p95 < 1.0:
            conclusions.append("✓ Good response times (P95 < 1s)")
        elif p95 < 2.0:
            conclusions.append("⚠ Acceptable but slow (P95 > 1s)")
        else:
            conclusions.append("✗ CRITICAL: Response times too high (P95 > 2s)")
        
        # Check error rates
        error_rate = error_count / total_requests if total_requests > 0 else 0
        if error_rate < 0.01:
            conclusions.append("✓ Excellent reliability (<1% errors)")
        elif error_rate < 0.05:
            conclusions.append("✓ Good reliability (<5% errors)")
        else:
            conclusions.append(f"✗ WARNING: High error rate ({error_rate*100:.1f}%)")
        
        # Check tail latency
        if p99 > mean * 3:
            conclusions.append("⚠ High tail latency (P99 is 3x mean) - investigate outliers")
        
        return conclusions


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class PerformanceMonitor:
    """Monitor API performance in production"""
    
    def __init__(self, db=None):
        self.db = db
        self.metrics = {}
    
    def track_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Track a request's performance"""
        key = f"{method} {endpoint}"
        
        if key not in self.metrics:
            self.metrics[key] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'errors': 0,
                'last_error': None
            }
        
        metrics = self.metrics[key]
        metrics['count'] += 1
        metrics['total_time'] += response_time
        metrics['min_time'] = min(metrics['min_time'], response_time)
        metrics['max_time'] = max(metrics['max_time'], response_time)
        
        if 400 <= status_code < 600:
            metrics['errors'] += 1
            metrics['last_error'] = datetime.utcnow()
    
    def get_endpoint_stats(self, endpoint: str = None) -> Dict:
        """Get statistics for endpoint(s)"""
        if endpoint:
            stats = self.metrics.get(endpoint, {})
            return self._calculate_stats(stats)
        
        all_stats = {}
        for ep, data in self.metrics.items():
            all_stats[ep] = self._calculate_stats(data)
        return all_stats
    
    def _calculate_stats(self, metric_data: Dict) -> Dict:
        """Calculate derived statistics"""
        if metric_data.get('count', 0) == 0:
            return {}
        
        count = metric_data['count']
        avg_time = metric_data['total_time'] / count
        error_rate = metric_data['errors'] / count
        
        return {
            'count': count,
            'avg_time_ms': avg_time * 1000,
            'min_time_ms': metric_data['min_time'] * 1000,
            'max_time_ms': metric_data['max_time'] * 1000,
            'error_rate': error_rate,
            'last_error': metric_data.get('last_error')
        }
    
    def get_health_status(self) -> Dict:
        """Get overall platform health"""
        all_stats = self.get_endpoint_stats()
        
        if not all_stats:
            return {'status': 'no_data'}
        
        # Calculate averages across endpoints
        avg_response_time = sum(
            s['avg_time_ms'] for s in all_stats.values()
        ) / len(all_stats)
        
        avg_error_rate = sum(
            s['error_rate'] for s in all_stats.values()
        ) / len(all_stats)
        
        # Determine health
        if avg_response_time < 500 and avg_error_rate < 0.01:
            status = 'HEALTHY'
            color = '✓'
        elif avg_response_time < 2000 and avg_error_rate < 0.05:
            status = 'DEGRADED'
            color = '⚠'
        else:
            status = 'CRITICAL'
            color = '✗'
        
        return {
            'status': status,
            'avg_response_time_ms': avg_response_time,
            'avg_error_rate': avg_error_rate,
            'endpoints_tracked': len(all_stats)
        }


# ============================================================================
# ALERTING
# ============================================================================

class AlertManager:
    """Generate alerts for performance issues"""
    
    # Alert thresholds
    THRESHOLDS = {
        'response_time_warning_ms': 1000,
        'response_time_critical_ms': 2000,
        'error_rate_warning': 0.05,
        'error_rate_critical': 0.10,
        'database_query_slow_ms': 1000,
        'cache_miss_rate_warning': 0.20
    }
    
    def __init__(self):
        self.active_alerts = []
    
    def check_response_time(self, endpoint: str, response_time: float) -> Optional[Dict]:
        """Alert if response time exceeds threshold"""
        if response_time > self.THRESHOLDS['response_time_critical_ms'] / 1000:
            return {
                'level': 'CRITICAL',
                'metric': 'response_time',
                'endpoint': endpoint,
                'value': response_time * 1000,
                'threshold': self.THRESHOLDS['response_time_critical_ms'],
                'message': f"{endpoint} response time critical: {response_time*1000:.0f}ms"
            }
        elif response_time > self.THRESHOLDS['response_time_warning_ms'] / 1000:
            return {
                'level': 'WARNING',
                'metric': 'response_time',
                'endpoint': endpoint,
                'value': response_time * 1000,
                'threshold': self.THRESHOLDS['response_time_warning_ms'],
                'message': f"{endpoint} response time slow: {response_time*1000:.0f}ms"
            }
        return None
    
    def check_error_rate(self, endpoint: str, error_rate: float) -> Optional[Dict]:
        """Alert if error rate exceeds threshold"""
        if error_rate > self.THRESHOLDS['error_rate_critical']:
            return {
                'level': 'CRITICAL',
                'metric': 'error_rate',
                'endpoint': endpoint,
                'value': error_rate,
                'threshold': self.THRESHOLDS['error_rate_critical'],
                'message': f"{endpoint} error rate critical: {error_rate*100:.1f}%"
            }
        elif error_rate > self.THRESHOLDS['error_rate_warning']:
            return {
                'level': 'WARNING',
                'metric': 'error_rate',
                'endpoint': endpoint,
                'value': error_rate,
                'threshold': self.THRESHOLDS['error_rate_warning'],
                'message': f"{endpoint} error rate elevated: {error_rate*100:.1f}%"
            }
        return None
    
    def generate_alert(self, alert_dict: Dict):
        """Generate and log an alert"""
        if alert_dict:
            alert_dict['timestamp'] = datetime.utcnow().isoformat()
            self.active_alerts.append(alert_dict)
            
            level = alert_dict['level']
            message = alert_dict['message']
            
            if level == 'CRITICAL':
                logger.critical(message)
            else:
                logger.warning(message)
            
            return alert_dict
        return None


# ============================================================================
# REQUEST TIMING DECORATOR
# ============================================================================

def monitor_performance(func):
    """Decorator to monitor request performance"""
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start
            endpoint = func.__name__
            logger.debug(f"{endpoint} took {elapsed*1000:.1f}ms")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start
            endpoint = func.__name__
            logger.debug(f"{endpoint} took {elapsed*1000:.1f}ms")
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

async def run_load_test_example():
    """Example load test execution"""
    runner = LoadTestRunner()
    
    report = await runner.run_prediction_Load_test(
        num_users=100,
        requests_per_user=10,
        ramp_up_seconds=30
    )
    
    print("\n" + "="*60)
    print("LOAD TEST REPORT")
    print("="*60)
    print(f"\nSummary:")
    for k, v in report.get('summary', {}).items():
        print(f"  {k}: {v}")
    print(f"\nResponse Time Stats:")
    for k, v in report.get('response_time_stats', {}).items():
        print(f"  {k}: {v:.2f}")
    print(f"\nConclusions:")
    for conclusion in report.get('conclusions', []):
        print(f"  {conclusion}")
    
    return report


def generate_monitoring_report(monitor: PerformanceMonitor) -> str:
    """Generate human-readable monitoring report"""
    stats = monitor.get_endpoint_stats()
    health = monitor.get_health_status()
    
    report = []
    report.append("\n" + "="*60)
    report.append("PLATFORM MONITORING REPORT")
    report.append("="*60)
    
    report.append(f"\nOverall Health: {health['status']}")
    report.append(f"Avg Response Time: {health.get('avg_response_time_ms', 0):.0f}ms")
    report.append(f"Avg Error Rate: {health.get('avg_error_rate', 0)*100:.2f}%")
    
    report.append(f"\n{'Endpoint':<40} {'Avg Time':<12} {'Error Rate':<12}")
    report.append("-" * 65)
    
    for endpoint, stat in stats.items():
        error_pct = stat.get('error_rate', 0) * 100
        avg_time = stat.get('avg_time_ms', 0)
        report.append(f"{endpoint:<40} {avg_time:>8.0f}ms  {error_pct:>8.2f}%")
    
    return "\n".join(report)
