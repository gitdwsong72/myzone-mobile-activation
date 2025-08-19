"""
헬스체크 및 장애 복구 시스템
"""
import asyncio
import time
import psutil
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from sqlalchemy import text
from app.core.database import get_db
from app.core.redis_client import get_redis_client
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger('health_check')

class HealthStatus(Enum):
    """헬스 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """헬스체크 결과"""
    service: str
    status: HealthStatus
    response_time: float
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

@dataclass
class SystemHealth:
    """시스템 전체 헬스 상태"""
    overall_status: HealthStatus
    timestamp: datetime
    services: List[HealthCheckResult]
    system_info: Dict[str, Any]

class HealthChecker:
    """헬스체크 수행 클래스"""
    
    def __init__(self):
        self.checks = {}
        self.last_results = {}
        self.failure_counts = {}
        
        # 기본 헬스체크 등록
        self.register_check("database", self._check_database)
        self.register_check("redis", self._check_redis)
        self.register_check("disk_space", self._check_disk_space)
        self.register_check("memory", self._check_memory)
        self.register_check("cpu", self._check_cpu)
    
    def register_check(self, name: str, check_func: Callable):
        """헬스체크 등록"""
        self.checks[name] = check_func
        self.failure_counts[name] = 0
        logger.info(f"Health check registered: {name}")
    
    async def run_all_checks(self) -> SystemHealth:
        """모든 헬스체크 실행"""
        results = []
        
        for name, check_func in self.checks.items():
            try:
                result = await self._run_single_check(name, check_func)
                results.append(result)
                self.last_results[name] = result
                
                # 실패 카운트 관리
                if result.status == HealthStatus.HEALTHY:
                    self.failure_counts[name] = 0
                else:
                    self.failure_counts[name] += 1
                    
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                result = HealthCheckResult(
                    service=name,
                    status=HealthStatus.UNKNOWN,
                    response_time=0.0,
                    message=f"Check failed: {str(e)}",
                    timestamp=datetime.now()
                )
                results.append(result)
                self.failure_counts[name] += 1
        
        # 전체 상태 결정
        overall_status = self._determine_overall_status(results)
        
        # 시스템 정보 수집
        system_info = self._collect_system_info()
        
        return SystemHealth(
            overall_status=overall_status,
            timestamp=datetime.now(),
            services=results,
            system_info=system_info
        )
    
    async def _run_single_check(self, name: str, check_func: Callable) -> HealthCheckResult:
        """단일 헬스체크 실행"""
        start_time = time.time()
        
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            response_time = time.time() - start_time
            
            if isinstance(result, HealthCheckResult):
                result.response_time = response_time
                return result
            else:
                return HealthCheckResult(
                    service=name,
                    status=HealthStatus.HEALTHY,
                    response_time=response_time,
                    message="OK",
                    timestamp=datetime.now(),
                    details=result if isinstance(result, dict) else None
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service=name,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=str(e),
                timestamp=datetime.now()
            )
    
    def _determine_overall_status(self, results: List[HealthCheckResult]) -> HealthStatus:
        """전체 상태 결정"""
        if not results:
            return HealthStatus.UNKNOWN
        
        unhealthy_count = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """시스템 정보 수집"""
        try:
            return {
                "uptime": time.time() - psutil.boot_time(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_total": psutil.disk_usage('/').total,
                "python_version": f"{psutil.version_info}",
                "environment": settings.ENVIRONMENT,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to collect system info: {e}")
            return {}
    
    # 개별 헬스체크 메서드들
    async def _check_database(self) -> HealthCheckResult:
        """데이터베이스 헬스체크"""
        try:
            db = next(get_db())
            start_time = time.time()
            
            # 간단한 쿼리 실행
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            
            response_time = time.time() - start_time
            
            # 연결 풀 상태 확인
            pool = db.get_bind().pool
            pool_status = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
            # 응답 시간 기반 상태 결정
            if response_time > 5.0:
                status = HealthStatus.UNHEALTHY
                message = f"Database response too slow: {response_time:.2f}s"
            elif response_time > 1.0:
                status = HealthStatus.DEGRADED
                message = f"Database response slow: {response_time:.2f}s"
            else:
                status = HealthStatus.HEALTHY
                message = "Database connection OK"
            
            return HealthCheckResult(
                service="database",
                status=status,
                response_time=response_time,
                message=message,
                timestamp=datetime.now(),
                details=pool_status
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="database",
                status=HealthStatus.UNHEALTHY,
                response_time=0.0,
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def _check_redis(self) -> HealthCheckResult:
        """Redis 헬스체크"""
        try:
            redis_client = get_redis_client()
            start_time = time.time()
            
            # PING 명령 실행
            pong = redis_client.ping()
            response_time = time.time() - start_time
            
            if not pong:
                return HealthCheckResult(
                    service="redis",
                    status=HealthStatus.UNHEALTHY,
                    response_time=response_time,
                    message="Redis PING failed",
                    timestamp=datetime.now()
                )
            
            # Redis 정보 수집
            info = redis_client.info()
            redis_details = {
                "version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses")
            }
            
            # 응답 시간 기반 상태 결정
            if response_time > 1.0:
                status = HealthStatus.DEGRADED
                message = f"Redis response slow: {response_time:.2f}s"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis connection OK"
            
            return HealthCheckResult(
                service="redis",
                status=status,
                response_time=response_time,
                message=message,
                timestamp=datetime.now(),
                details=redis_details
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="redis",
                status=HealthStatus.UNHEALTHY,
                response_time=0.0,
                message=f"Redis connection failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def _check_disk_space(self) -> HealthCheckResult:
        """디스크 공간 헬스체크"""
        try:
            disk_usage = psutil.disk_usage('/')
            used_percent = (disk_usage.used / disk_usage.total) * 100
            
            details = {
                "total_gb": round(disk_usage.total / (1024**3), 2),
                "used_gb": round(disk_usage.used / (1024**3), 2),
                "free_gb": round(disk_usage.free / (1024**3), 2),
                "used_percent": round(used_percent, 2)
            }
            
            if used_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"Disk space critically low: {used_percent:.1f}% used"
            elif used_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"Disk space low: {used_percent:.1f}% used"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk space OK: {used_percent:.1f}% used"
            
            return HealthCheckResult(
                service="disk_space",
                status=status,
                response_time=0.0,
                message=message,
                timestamp=datetime.now(),
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="disk_space",
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                message=f"Disk check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def _check_memory(self) -> HealthCheckResult:
        """메모리 헬스체크"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            details = {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": round(used_percent, 2)
            }
            
            if used_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage critically high: {used_percent:.1f}%"
            elif used_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Memory usage high: {used_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage OK: {used_percent:.1f}%"
            
            return HealthCheckResult(
                service="memory",
                status=status,
                response_time=0.0,
                message=message,
                timestamp=datetime.now(),
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="memory",
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                message=f"Memory check failed: {str(e)}",
                timestamp=datetime.now()
            )
    
    def _check_cpu(self) -> HealthCheckResult:
        """CPU 헬스체크"""
        try:
            # 1초 간격으로 CPU 사용률 측정
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            details = {
                "cpu_percent": round(cpu_percent, 2),
                "cpu_count": cpu_count,
                "load_avg_1m": round(load_avg[0], 2),
                "load_avg_5m": round(load_avg[1], 2),
                "load_avg_15m": round(load_avg[2], 2)
            }
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"CPU usage critically high: {cpu_percent:.1f}%"
            elif cpu_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"CPU usage high: {cpu_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage OK: {cpu_percent:.1f}%"
            
            return HealthCheckResult(
                service="cpu",
                status=status,
                response_time=0.0,
                message=message,
                timestamp=datetime.now(),
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                service="cpu",
                status=HealthStatus.UNKNOWN,
                response_time=0.0,
                message=f"CPU check failed: {str(e)}",
                timestamp=datetime.now()
            )

class FailureRecovery:
    """장애 복구 시스템"""
    
    def __init__(self, health_checker: HealthChecker):
        self.health_checker = health_checker
        self.recovery_actions = {}
        self.recovery_history = []
        
        # 기본 복구 액션 등록
        self.register_recovery("database", self._recover_database)
        self.register_recovery("redis", self._recover_redis)
        self.register_recovery("memory", self._recover_memory)
    
    def register_recovery(self, service: str, recovery_func: Callable):
        """복구 액션 등록"""
        self.recovery_actions[service] = recovery_func
        logger.info(f"Recovery action registered for: {service}")
    
    async def attempt_recovery(self, service: str) -> bool:
        """복구 시도"""
        if service not in self.recovery_actions:
            logger.warning(f"No recovery action available for: {service}")
            return False
        
        try:
            logger.info(f"Attempting recovery for: {service}")
            recovery_func = self.recovery_actions[service]
            
            if asyncio.iscoroutinefunction(recovery_func):
                success = await recovery_func()
            else:
                success = recovery_func()
            
            # 복구 이력 기록
            self.recovery_history.append({
                "service": service,
                "timestamp": datetime.now(),
                "success": success
            })
            
            if success:
                logger.info(f"Recovery successful for: {service}")
            else:
                logger.error(f"Recovery failed for: {service}")
            
            return success
            
        except Exception as e:
            logger.error(f"Recovery attempt failed for {service}: {e}")
            self.recovery_history.append({
                "service": service,
                "timestamp": datetime.now(),
                "success": False,
                "error": str(e)
            })
            return False
    
    async def _recover_database(self) -> bool:
        """데이터베이스 복구"""
        try:
            # 연결 풀 재시작
            from app.core.database import engine
            engine.dispose()
            
            # 연결 테스트
            db = next(get_db())
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            
            return True
        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            return False
    
    async def _recover_redis(self) -> bool:
        """Redis 복구"""
        try:
            # Redis 연결 재시작
            redis_client = get_redis_client()
            redis_client.connection_pool.disconnect()
            
            # 연결 테스트
            pong = redis_client.ping()
            return bool(pong)
        except Exception as e:
            logger.error(f"Redis recovery failed: {e}")
            return False
    
    def _recover_memory(self) -> bool:
        """메모리 복구 (가비지 컬렉션)"""
        try:
            import gc
            collected = gc.collect()
            logger.info(f"Garbage collection completed: {collected} objects collected")
            return True
        except Exception as e:
            logger.error(f"Memory recovery failed: {e}")
            return False

class HealthMonitor:
    """헬스 모니터링 서비스"""
    
    def __init__(self, check_interval: int = 60):
        self.health_checker = HealthChecker()
        self.failure_recovery = FailureRecovery(self.health_checker)
        self.check_interval = check_interval
        self.is_running = False
        self.consecutive_failures = {}
        self.max_failures = 3  # 연속 실패 임계값
    
    async def start_monitoring(self):
        """모니터링 시작"""
        self.is_running = True
        logger.info("Health monitoring started")
        
        while self.is_running:
            try:
                # 헬스체크 실행
                health = await self.health_checker.run_all_checks()
                
                # 실패한 서비스 처리
                await self._handle_failures(health)
                
                # 전체 상태 로깅
                logger.info(
                    f"Health check completed: {health.overall_status.value}",
                    extra={
                        "overall_status": health.overall_status.value,
                        "services_count": len(health.services),
                        "unhealthy_services": [
                            s.service for s in health.services 
                            if s.status == HealthStatus.UNHEALTHY
                        ]
                    }
                )
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        logger.info("Health monitoring stopped")
    
    async def _handle_failures(self, health: SystemHealth):
        """실패 처리"""
        for service_result in health.services:
            service_name = service_result.service
            
            if service_result.status == HealthStatus.UNHEALTHY:
                # 연속 실패 카운트 증가
                self.consecutive_failures[service_name] = \
                    self.consecutive_failures.get(service_name, 0) + 1
                
                # 임계값 도달 시 복구 시도
                if self.consecutive_failures[service_name] >= self.max_failures:
                    logger.warning(
                        f"Service {service_name} failed {self.consecutive_failures[service_name]} times consecutively"
                    )
                    
                    # 복구 시도
                    recovery_success = await self.failure_recovery.attempt_recovery(service_name)
                    
                    if recovery_success:
                        self.consecutive_failures[service_name] = 0
                    else:
                        # 복구 실패 시 알림
                        logger.critical(
                            f"Failed to recover service: {service_name}",
                            extra={
                                "service": service_name,
                                "consecutive_failures": self.consecutive_failures[service_name],
                                "alert_type": "recovery_failed"
                            }
                        )
            else:
                # 정상 상태면 실패 카운트 리셋
                self.consecutive_failures[service_name] = 0

# 전역 인스턴스
health_checker = HealthChecker()
failure_recovery = FailureRecovery(health_checker)
health_monitor = HealthMonitor(check_interval=60)