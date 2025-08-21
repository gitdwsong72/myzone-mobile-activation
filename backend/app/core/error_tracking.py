"""
오류 추적 및 알림 시스템
"""

import hashlib
import logging
import traceback
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.logging_config import get_logger
from app.core.redis_client import redis_client

logger = get_logger("error_tracking")


@dataclass
class ErrorInfo:
    """오류 정보 데이터 클래스"""

    error_id: str
    timestamp: datetime
    error_type: str
    error_message: str
    traceback: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    stack_hash: Optional[str] = None
    severity: str = "error"
    tags: Optional[Dict[str, str]] = None


@dataclass
class ErrorSummary:
    """오류 요약 정보"""

    error_hash: str
    error_type: str
    error_message: str
    first_seen: datetime
    last_seen: datetime
    count: int
    affected_users: int
    endpoints: List[str]
    severity: str


class ErrorTracker:
    """오류 추적기"""

    def __init__(self):
        self.redis_client = redis_client
        self.error_cache = deque(maxlen=1000)  # 최근 1000개 오류 캐시
        self.error_counts = defaultdict(int)
        self.error_summaries = {}

        # 오류 심각도 매핑
        self.severity_mapping = {
            "critical": ["SystemExit", "KeyboardInterrupt", "MemoryError"],
            "high": ["DatabaseError", "ConnectionError", "TimeoutError"],
            "medium": ["ValidationError", "PermissionError", "FileNotFoundError"],
            "low": ["Warning", "DeprecationWarning"],
        }

    def track_error(
        self,
        error: Exception,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """오류 추적"""
        try:
            # 오류 정보 생성
            error_info = self._create_error_info(error, endpoint, method, user_id, ip_address, user_agent, request_data, tags)

            # 캐시에 저장
            self.error_cache.append(error_info)

            # Redis에 저장
            if self.redis_client:
                self._store_error_in_redis(error_info)

            # 오류 요약 업데이트
            self._update_error_summary(error_info)

            # 알림 확인
            self._check_error_alerts(error_info)

            # 로그 기록
            self._log_error(error_info)

            return error_info.error_id

        except Exception as e:
            logger.error(f"Failed to track error: {e}")
            return ""

    def _create_error_info(
        self,
        error: Exception,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> ErrorInfo:
        """오류 정보 생성"""
        # 트레이스백 정보
        tb_str = traceback.format_exc()

        # 스택 해시 생성 (동일한 오류 그룹화용)
        stack_hash = self._generate_stack_hash(error, tb_str)

        # 오류 ID 생성
        error_id = self._generate_error_id(error, stack_hash)

        # 심각도 결정
        severity = self._determine_severity(error)

        return ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=tb_str,
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data=request_data,
            stack_hash=stack_hash,
            severity=severity,
            tags=tags or {},
        )

    def _generate_stack_hash(self, error: Exception, traceback_str: str) -> str:
        """스택 해시 생성"""
        # 트레이스백에서 파일 경로와 라인 번호 추출
        lines = traceback_str.split("\n")
        relevant_lines = []

        for line in lines:
            if 'File "' in line and "line" in line:
                # 파일 경로에서 프로젝트 루트 이후 부분만 사용
                if "/app/" in line:
                    line = line.split("/app/")[-1]
                relevant_lines.append(line.strip())

        # 오류 타입과 관련 스택 정보로 해시 생성
        hash_content = f"{type(error).__name__}:{'|'.join(relevant_lines)}"
        return hashlib.md5(hash_content.encode()).hexdigest()[:16]

    def _generate_error_id(self, error: Exception, stack_hash: str) -> str:
        """오류 ID 생성"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{type(error).__name__}_{stack_hash}_{timestamp}"

    def _determine_severity(self, error: Exception) -> str:
        """오류 심각도 결정"""
        error_type = type(error).__name__

        for severity, error_types in self.severity_mapping.items():
            if error_type in error_types:
                return severity

        # HTTP 상태 코드 기반 심각도
        if hasattr(error, "status_code"):
            status_code = error.status_code
            if status_code >= 500:
                return "high"
            elif status_code >= 400:
                return "medium"

        return "medium"  # 기본값

    def _store_error_in_redis(self, error_info: ErrorInfo):
        """Redis에 오류 정보 저장"""
        try:
            # 개별 오류 저장
            key = f"errors:individual:{error_info.error_id}"
            data = asdict(error_info)
            data["timestamp"] = error_info.timestamp.isoformat()

            self.redis_client.setex(key, 86400 * 30, str(data))  # 30일 보관

            # 오류 해시별 카운트 증가
            hash_key = f"errors:count:{error_info.stack_hash}"
            self.redis_client.incr(hash_key)
            self.redis_client.expire(hash_key, 86400 * 30)

            # 시간별 오류 통계
            hour_key = f"errors:hourly:{datetime.now().strftime('%Y%m%d%H')}"
            self.redis_client.incr(hour_key)
            self.redis_client.expire(hour_key, 86400 * 7)  # 7일 보관

        except Exception as e:
            logger.error(f"Failed to store error in Redis: {e}")

    def _update_error_summary(self, error_info: ErrorInfo):
        """오류 요약 업데이트"""
        hash_key = error_info.stack_hash

        if hash_key in self.error_summaries:
            summary = self.error_summaries[hash_key]
            summary.last_seen = error_info.timestamp
            summary.count += 1

            if error_info.user_id:
                # 영향받은 사용자 수는 실제로는 Set을 사용해야 함
                pass

            if error_info.endpoint and error_info.endpoint not in summary.endpoints:
                summary.endpoints.append(error_info.endpoint)
        else:
            self.error_summaries[hash_key] = ErrorSummary(
                error_hash=hash_key,
                error_type=error_info.error_type,
                error_message=error_info.error_message,
                first_seen=error_info.timestamp,
                last_seen=error_info.timestamp,
                count=1,
                affected_users=1 if error_info.user_id else 0,
                endpoints=[error_info.endpoint] if error_info.endpoint else [],
                severity=error_info.severity,
            )

    def _check_error_alerts(self, error_info: ErrorInfo):
        """오류 알림 확인"""
        # 심각한 오류는 즉시 알림
        if error_info.severity == "critical":
            self._send_immediate_alert(error_info)

        # 동일한 오류가 짧은 시간에 반복되면 알림
        hash_key = error_info.stack_hash
        if hash_key in self.error_summaries:
            summary = self.error_summaries[hash_key]

            # 5분 내에 10회 이상 발생하면 알림
            if summary.count >= 10:
                time_diff = error_info.timestamp - summary.first_seen
                if time_diff <= timedelta(minutes=5):
                    self._send_frequency_alert(error_info, summary)

    def _send_immediate_alert(self, error_info: ErrorInfo):
        """즉시 알림 발송"""
        logger.critical(
            f"CRITICAL ERROR: {error_info.error_type}: {error_info.error_message}",
            extra={
                "alert_type": "critical_error",
                "error_id": error_info.error_id,
                "error_type": error_info.error_type,
                "endpoint": error_info.endpoint,
                "user_id": error_info.user_id,
            },
        )

    def _send_frequency_alert(self, error_info: ErrorInfo, summary: ErrorSummary):
        """빈도 기반 알림 발송"""
        logger.warning(
            f"FREQUENT ERROR: {error_info.error_type} occurred {summary.count} times",
            extra={
                "alert_type": "frequent_error",
                "error_hash": error_info.stack_hash,
                "error_type": error_info.error_type,
                "count": summary.count,
                "endpoints": summary.endpoints,
            },
        )

    def _log_error(self, error_info: ErrorInfo):
        """오류 로그 기록"""
        log_level = {"critical": logging.CRITICAL, "high": logging.ERROR, "medium": logging.WARNING, "low": logging.INFO}.get(
            error_info.severity, logging.ERROR
        )

        logger.log(
            log_level,
            f"Error tracked: {error_info.error_type}: {error_info.error_message}",
            extra={
                "error_id": error_info.error_id,
                "error_type": error_info.error_type,
                "stack_hash": error_info.stack_hash,
                "endpoint": error_info.endpoint,
                "method": error_info.method,
                "user_id": error_info.user_id,
                "ip_address": error_info.ip_address,
                "severity": error_info.severity,
                "tags": error_info.tags,
            },
        )

    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """오류 통계 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_cache if e.timestamp >= cutoff_time]

        if not recent_errors:
            return {"total_errors": 0, "error_rate": 0, "top_errors": [], "severity_distribution": {}}

        # 오류 타입별 집계
        error_type_counts = defaultdict(int)
        severity_counts = defaultdict(int)

        for error in recent_errors:
            error_type_counts[error.error_type] += 1
            severity_counts[error.severity] += 1

        # 상위 오류 타입
        top_errors = sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_errors": len(recent_errors),
            "error_rate": len(recent_errors) / hours,
            "top_errors": [{"type": error_type, "count": count} for error_type, count in top_errors],
            "severity_distribution": dict(severity_counts),
            "unique_errors": len(set(e.stack_hash for e in recent_errors)),
        }

    def get_error_details(self, error_id: str) -> Optional[ErrorInfo]:
        """오류 상세 정보 조회"""
        # 캐시에서 먼저 확인
        for error in self.error_cache:
            if error.error_id == error_id:
                return error

        # Redis에서 조회
        if self.redis_client:
            try:
                key = f"errors:individual:{error_id}"
                data = self.redis_client.get(key)
                if data:
                    # 실제로는 JSON 파싱이 필요
                    pass
            except Exception as e:
                logger.error(f"Failed to get error details from Redis: {e}")

        return None

    def get_similar_errors(self, stack_hash: str, limit: int = 10) -> List[ErrorInfo]:
        """유사한 오류 조회"""
        similar_errors = [error for error in self.error_cache if error.stack_hash == stack_hash]

        return sorted(similar_errors, key=lambda x: x.timestamp, reverse=True)[:limit]


class ErrorReporter:
    """오류 리포터"""

    def __init__(self, error_tracker: ErrorTracker):
        self.error_tracker = error_tracker

    def generate_error_report(self, hours: int = 24) -> Dict[str, Any]:
        """오류 리포트 생성"""
        stats = self.error_tracker.get_error_statistics(hours)

        # 추가 분석
        report = {
            "period": f"Last {hours} hours",
            "generated_at": datetime.now().isoformat(),
            "summary": stats,
            "recommendations": self._generate_recommendations(stats),
            "trending_errors": self._get_trending_errors(),
            "affected_endpoints": self._get_affected_endpoints(),
        }

        return report

    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """개선 권장사항 생성"""
        recommendations = []

        if stats["total_errors"] > 100:
            recommendations.append("High error rate detected. Consider reviewing recent deployments.")

        if stats["severity_distribution"].get("critical", 0) > 0:
            recommendations.append("Critical errors detected. Immediate attention required.")

        # 상위 오류 타입 기반 권장사항
        top_errors = stats.get("top_errors", [])
        if top_errors:
            top_error_type = top_errors[0]["type"]
            if top_error_type == "ValidationError":
                recommendations.append("Consider improving input validation.")
            elif top_error_type == "DatabaseError":
                recommendations.append("Check database connection and query performance.")
            elif top_error_type == "TimeoutError":
                recommendations.append("Review timeout settings and external service dependencies.")

        return recommendations

    def _get_trending_errors(self) -> List[Dict[str, Any]]:
        """트렌딩 오류 조회"""
        # 실제로는 시간대별 오류 증가율을 계산해야 함
        return []

    def _get_affected_endpoints(self) -> List[Dict[str, Any]]:
        """영향받은 엔드포인트 조회"""
        endpoint_errors = defaultdict(int)

        for error in self.error_tracker.error_cache:
            if error.endpoint:
                endpoint_errors[error.endpoint] += 1

        sorted_endpoints = sorted(endpoint_errors.items(), key=lambda x: x[1], reverse=True)

        return [{"endpoint": endpoint, "error_count": count} for endpoint, count in sorted_endpoints[:10]]


# 전역 오류 추적기 인스턴스
error_tracker = ErrorTracker()
error_reporter = ErrorReporter(error_tracker)
