"""
헬스체크 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from datetime import datetime

from app.core.health_check import health_checker, health_monitor, HealthStatus
from app.core.monitoring import metrics_collector
from app.core.error_tracking import error_tracker, error_reporter
from app.core.deps import get_current_admin_user
from app.schemas.admin import AdminResponse

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def basic_health_check():
    """기본 헬스체크 - 인증 불필요"""
    try:
        # 간단한 상태 확인
        health = await health_checker.run_all_checks()
        
        # 기본 정보만 반환
        return {
            "status": health.overall_status.value,
            "timestamp": health.timestamp.isoformat(),
            "message": "Service is running"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(
    current_admin: AdminResponse = Depends(get_current_admin_user)
):
    """상세 헬스체크 - 관리자 권한 필요"""
    try:
        health = await health_checker.run_all_checks()
        
        # 서비스별 상세 정보
        services_detail = []
        for service in health.services:
            service_info = {
                "service": service.service,
                "status": service.status.value,
                "response_time": round(service.response_time, 4),
                "message": service.message,
                "timestamp": service.timestamp.isoformat()
            }
            
            if service.details:
                service_info["details"] = service.details
            
            services_detail.append(service_info)
        
        return {
            "overall_status": health.overall_status.value,
            "timestamp": health.timestamp.isoformat(),
            "services": services_detail,
            "system_info": health.system_info,
            "failure_counts": health_checker.failure_counts
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detailed health check failed: {str(e)}"
        )

@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics(
    hours: int = 1,
    current_admin: AdminResponse = Depends(get_current_admin_user)
):
    """시스템 메트릭 조회"""
    try:
        # 요청 통계
        request_stats = metrics_collector.get_request_stats(minutes=hours * 60)
        
        # 시스템 통계
        system_stats = metrics_collector.get_system_stats()
        
        # 오류 통계
        error_stats = error_tracker.get_error_statistics(hours=hours)
        
        return {
            "period": f"Last {hours} hour(s)",
            "timestamp": datetime.now().isoformat(),
            "request_metrics": request_stats,
            "system_metrics": system_stats,
            "error_metrics": error_stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )

@router.get("/errors", response_model=Dict[str, Any])
async def get_error_report(
    hours: int = 24,
    current_admin: AdminResponse = Depends(get_current_admin_user)
):
    """오류 리포트 조회"""
    try:
        report = error_reporter.generate_error_report(hours=hours)
        return report
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate error report: {str(e)}"
        )

@router.get("/errors/{error_id}", response_model=Dict[str, Any])
async def get_error_details(
    error_id: str,
    current_admin: AdminResponse = Depends(get_current_admin_user)
):
    """특정 오류 상세 정보 조회"""
    try:
        error_info = error_tracker.get_error_details(error_id)
        
        if not error_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Error not found"
            )
        
        # 유사한 오류들도 함께 조회
        similar_errors = error_tracker.get_similar_errors(
            error_info.stack_hash, limit=5
        )
        
        return {
            "error_info": {
                "error_id": error_info.error_id,
                "timestamp": error_info.timestamp.isoformat(),
                "error_type": error_info.error_type,
                "error_message": error_info.error_message,
                "traceback": error_info.traceback,
                "endpoint": error_info.endpoint,
                "method": error_info.method,
                "user_id": error_info.user_id,
                "ip_address": error_info.ip_address,
                "severity": error_info.severity,
                "tags": error_info.tags
            },
            "similar_errors": [
                {
                    "error_id": e.error_id,
                    "timestamp": e.timestamp.isoformat(),
                    "error_message": e.error_message,
                    "endpoint": e.endpoint,
                    "user_id": e.user_id
                }
                for e in similar_errors
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error details: {str(e)}"
        )

@router.post("/recovery/{service}", response_model=Dict[str, Any])
async def trigger_recovery(
    service: str,
    current_admin: AdminResponse = Depends(get_current_admin_user)
):
    """수동 복구 트리거"""
    try:
        success = await health_monitor.failure_recovery.attempt_recovery(service)
        
        return {
            "service": service,
            "recovery_attempted": True,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "message": f"Recovery {'successful' if success else 'failed'} for {service}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recovery attempt failed: {str(e)}"
        )

@router.get("/monitoring/status", response_model=Dict[str, Any])
async def get_monitoring_status(
    current_admin: AdminResponse = Depends(get_current_admin_user)
):
    """모니터링 시스템 상태 조회"""
    try:
        return {
            "health_monitoring": {
                "is_running": health_monitor.is_running,
                "check_interval": health_monitor.check_interval,
                "consecutive_failures": health_monitor.consecutive_failures,
                "max_failures": health_monitor.max_failures
            },
            "registered_checks": list(health_checker.checks.keys()),
            "registered_recoveries": list(health_monitor.failure_recovery.recovery_actions.keys()),
            "recovery_history": health_monitor.failure_recovery.recovery_history[-10:],  # 최근 10개
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring status: {str(e)}"
        )

@router.get("/liveness")
async def liveness_probe():
    """Kubernetes liveness probe용 엔드포인트"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@router.get("/readiness")
async def readiness_probe():
    """Kubernetes readiness probe용 엔드포인트"""
    try:
        # 핵심 서비스들만 빠르게 체크
        db_check = await health_checker._check_database()
        redis_check = await health_checker._check_redis()
        
        if (db_check.status == HealthStatus.HEALTHY and 
            redis_check.status == HealthStatus.HEALTHY):
            return {
                "status": "ready",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )