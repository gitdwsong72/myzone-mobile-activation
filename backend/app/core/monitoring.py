"""
모니터링 및 메트릭 수집 시스템
"""
import time
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.core.redis_client import redis_client
from app.core.logging_config import get_logger

logger = get_logger('monitoring')

@dataclass
class RequestMetric:
    """요청 메트릭 데이터 클래스"""
    timestamp: datetime
    method: str
    endpoint: str
    status_code: int
    response_time: float
    request_size: int
    response_size: int
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class SystemMetric:
    """시스템 메트릭 데이터 클래스"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_available: int
    disk_percent: float
    disk_used: int
    disk_free: int
    network_sent: int
    network_recv: int
    active_connections: int

class MetricsCollector:
    """메트릭 수집기"""
    
    def __init__(self):
        self.redis_client = redis_client
        self.request_metrics = deque(maxlen=10000)  # 최근 10,000개 요청 보관
        self.system_metrics = deque(maxlen=1440)    # 24시간 (분당 1개)
        self.error_counts = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'error_count': 0
        })
    
    def record_request(self, metric: RequestMetric):
        """요청 메트릭 기록"""
        try:
            # 메모리에 저장
            self.request_metrics.append(metric)
            
            # 엔드포인트 통계 업데이트
            endpoint_key = f"{metric.method}:{metric.endpoint}"
            stats = self.endpoint_stats[endpoint_key]
            stats['count'] += 1
            stats['total_time'] += metric.response_time
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['min_time'] = min(stats['min_time'], metric.response_time)
            stats['max_time'] = max(stats['max_time'], metric.response_time)
            
            if metric.status_code >= 400:
                stats['error_count'] += 1
                self.error_counts[metric.status_code] += 1
            
            # Redis에 저장 (선택적)
            if self.redis_client:
                self._store_metric_in_redis(metric)
            
            # 로그 기록
            logger.info(
                f"Request processed: {metric.method} {metric.endpoint}",
                extra={
                    'method': metric.method,
                    'endpoint': metric.endpoint,
                    'status_code': metric.status_code,
                    'response_time': metric.response_time,
                    'user_id': metric.user_id,
                    'ip_address': metric.ip_address
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to record request metric: {e}")
    
    def record_system_metric(self, metric: SystemMetric):
        """시스템 메트릭 기록"""
        try:
            self.system_metrics.append(metric)
            
            # Redis에 저장
            if self.redis_client:
                self._store_system_metric_in_redis(metric)
            
            # 임계값 확인 및 알림
            self._check_system_thresholds(metric)
            
        except Exception as e:
            logger.error(f"Failed to record system metric: {e}")
    
    def _store_metric_in_redis(self, metric: RequestMetric):
        """Redis에 요청 메트릭 저장"""
        try:
            key = f"metrics:requests:{datetime.now().strftime('%Y%m%d%H')}"
            data = asdict(metric)
            data['timestamp'] = metric.timestamp.isoformat()
            
            self.redis_client.lpush(key, str(data))
            self.redis_client.expire(key, 86400 * 7)  # 7일 보관
            
        except Exception as e:
            logger.error(f"Failed to store metric in Redis: {e}")
    
    def _store_system_metric_in_redis(self, metric: SystemMetric):
        """Redis에 시스템 메트릭 저장"""
        try:
            key = f"metrics:system:{datetime.now().strftime('%Y%m%d%H%M')}"
            data = asdict(metric)
            data['timestamp'] = metric.timestamp.isoformat()
            
            self.redis_client.set(key, str(data), ex=86400 * 7)  # 7일 보관
            
        except Exception as e:
            logger.error(f"Failed to store system metric in Redis: {e}")
    
    def _check_system_thresholds(self, metric: SystemMetric):
        """시스템 임계값 확인"""
        alerts = []
        
        if metric.cpu_percent > 80:
            alerts.append(f"High CPU usage: {metric.cpu_percent:.1f}%")
        
        if metric.memory_percent > 85:
            alerts.append(f"High memory usage: {metric.memory_percent:.1f}%")
        
        if metric.disk_percent > 90:
            alerts.append(f"High disk usage: {metric.disk_percent:.1f}%")
        
        for alert in alerts:
            logger.warning(alert, extra={'alert_type': 'system_threshold'})
    
    def get_request_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """요청 통계 조회"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [m for m in self.request_metrics if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {
                'total_requests': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'requests_per_minute': 0
            }
        
        total_requests = len(recent_metrics)
        total_response_time = sum(m.response_time for m in recent_metrics)
        error_count = sum(1 for m in recent_metrics if m.status_code >= 400)
        
        return {
            'total_requests': total_requests,
            'avg_response_time': total_response_time / total_requests,
            'error_rate': (error_count / total_requests) * 100,
            'requests_per_minute': total_requests / minutes,
            'status_codes': self._get_status_code_distribution(recent_metrics),
            'top_endpoints': self._get_top_endpoints(recent_metrics)
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 조회"""
        if not self.system_metrics:
            return {}
        
        latest = self.system_metrics[-1]
        return {
            'cpu_percent': latest.cpu_percent,
            'memory_percent': latest.memory_percent,
            'memory_used_gb': latest.memory_used / (1024**3),
            'memory_available_gb': latest.memory_available / (1024**3),
            'disk_percent': latest.disk_percent,
            'disk_used_gb': latest.disk_used / (1024**3),
            'disk_free_gb': latest.disk_free / (1024**3),
            'active_connections': latest.active_connections
        }
    
    def _get_status_code_distribution(self, metrics: List[RequestMetric]) -> Dict[str, int]:
        """상태 코드 분포"""
        distribution = defaultdict(int)
        for metric in metrics:
            status_range = f"{metric.status_code // 100}xx"
            distribution[status_range] += 1
        return dict(distribution)
    
    def _get_top_endpoints(self, metrics: List[RequestMetric], limit: int = 10) -> List[Dict[str, Any]]:
        """상위 엔드포인트"""
        endpoint_counts = defaultdict(int)
        for metric in metrics:
            endpoint_key = f"{metric.method} {metric.endpoint}"
            endpoint_counts[endpoint_key] += 1
        
        sorted_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {'endpoint': endpoint, 'count': count}
            for endpoint, count in sorted_endpoints[:limit]
        ]

class MonitoringMiddleware(BaseHTTPMiddleware):
    """모니터링 미들웨어"""
    
    def __init__(self, app, metrics_collector: MetricsCollector):
        super().__init__(app)
        self.metrics_collector = metrics_collector
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # 요청 정보 수집
        method = request.method
        endpoint = request.url.path
        request_size = int(request.headers.get('content-length', 0))
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get('user-agent', '')
        user_id = getattr(request.state, 'user_id', None)
        
        response = None
        error_message = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            response_size = len(response.body) if hasattr(response, 'body') else 0
            
        except Exception as e:
            status_code = 500
            response_size = 0
            error_message = str(e)
            logger.error(f"Request processing error: {e}", exc_info=True)
            raise
        
        finally:
            # 응답 시간 계산
            response_time = time.time() - start_time
            
            # 메트릭 기록
            metric = RequestMetric(
                timestamp=datetime.now(),
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                response_time=response_time,
                request_size=request_size,
                response_size=response_size,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message=error_message
            )
            
            self.metrics_collector.record_request(metric)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 추출"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

class SystemMonitor:
    """시스템 모니터"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.is_running = False
    
    async def start_monitoring(self, interval: int = 60):
        """시스템 모니터링 시작"""
        self.is_running = True
        logger.info("System monitoring started")
        
        while self.is_running:
            try:
                metric = self._collect_system_metrics()
                self.metrics_collector.record_system_metric(metric)
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """시스템 모니터링 중지"""
        self.is_running = False
        logger.info("System monitoring stopped")
    
    def _collect_system_metrics(self) -> SystemMetric:
        """시스템 메트릭 수집"""
        # CPU 사용률
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 메모리 정보
        memory = psutil.virtual_memory()
        
        # 디스크 정보
        disk = psutil.disk_usage('/')
        
        # 네트워크 정보
        network = psutil.net_io_counters()
        
        # 활성 연결 수
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            connections = 0
        
        return SystemMetric(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used=memory.used,
            memory_available=memory.available,
            disk_percent=disk.percent,
            disk_used=disk.used,
            disk_free=disk.free,
            network_sent=network.bytes_sent,
            network_recv=network.bytes_recv,
            active_connections=connections
        )

class AlertManager:
    """알림 관리자"""
    
    def __init__(self):
        self.alert_thresholds = {
            'response_time': 5.0,  # 5초
            'error_rate': 10.0,    # 10%
            'cpu_usage': 80.0,     # 80%
            'memory_usage': 85.0,  # 85%
            'disk_usage': 90.0,    # 90%
        }
        self.alert_cooldown = 300  # 5분
        self.last_alerts = {}
    
    def check_alerts(self, metrics_collector: MetricsCollector):
        """알림 확인"""
        current_time = time.time()
        
        # 요청 관련 알림
        request_stats = metrics_collector.get_request_stats(minutes=5)
        
        if request_stats['avg_response_time'] > self.alert_thresholds['response_time']:
            self._send_alert(
                'high_response_time',
                f"High average response time: {request_stats['avg_response_time']:.2f}s",
                current_time
            )
        
        if request_stats['error_rate'] > self.alert_thresholds['error_rate']:
            self._send_alert(
                'high_error_rate',
                f"High error rate: {request_stats['error_rate']:.1f}%",
                current_time
            )
        
        # 시스템 관련 알림
        system_stats = metrics_collector.get_system_stats()
        
        if system_stats.get('cpu_percent', 0) > self.alert_thresholds['cpu_usage']:
            self._send_alert(
                'high_cpu_usage',
                f"High CPU usage: {system_stats['cpu_percent']:.1f}%",
                current_time
            )
        
        if system_stats.get('memory_percent', 0) > self.alert_thresholds['memory_usage']:
            self._send_alert(
                'high_memory_usage',
                f"High memory usage: {system_stats['memory_percent']:.1f}%",
                current_time
            )
        
        if system_stats.get('disk_percent', 0) > self.alert_thresholds['disk_usage']:
            self._send_alert(
                'high_disk_usage',
                f"High disk usage: {system_stats['disk_percent']:.1f}%",
                current_time
            )
    
    def _send_alert(self, alert_type: str, message: str, current_time: float):
        """알림 발송"""
        # 쿨다운 확인
        if alert_type in self.last_alerts:
            if current_time - self.last_alerts[alert_type] < self.alert_cooldown:
                return
        
        self.last_alerts[alert_type] = current_time
        
        # 로그에 알림 기록
        logger.critical(
            f"ALERT: {message}",
            extra={
                'alert_type': alert_type,
                'alert_message': message,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        # 여기에 실제 알림 발송 로직 추가 (이메일, Slack 등)
        # self._send_email_alert(alert_type, message)
        # self._send_slack_alert(alert_type, message)

# 전역 메트릭 수집기 인스턴스
metrics_collector = MetricsCollector()
system_monitor = SystemMonitor(metrics_collector)
alert_manager = AlertManager()