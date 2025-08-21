"""
캐싱 서비스 - Redis를 이용한 데이터 캐싱
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from ..core.redis_client import redis_client

logger = logging.getLogger(__name__)


class CacheService:
    """캐싱 서비스 클래스"""

    # 캐시 키 프리픽스
    PREFIXES = {
        "plan": "plan:",
        "device": "device:",
        "number": "number:",
        "user": "user:",
        "order": "order:",
        "session": "session:",
        "stats": "stats:",
        "search": "search:",
        "temp": "temp:",
    }

    # 기본 TTL (초)
    DEFAULT_TTL = {
        "plan": 3600,  # 1시간
        "device": 1800,  # 30분
        "number": 300,  # 5분
        "user": 1800,  # 30분
        "order": 600,  # 10분
        "session": 86400,  # 24시간
        "stats": 300,  # 5분
        "search": 600,  # 10분
        "temp": 300,  # 5분
    }

    def __init__(self):
        self.client = redis_client

    def _get_key(self, prefix: str, identifier: str) -> str:
        """캐시 키 생성"""
        return f"{self.PREFIXES.get(prefix, prefix)}{identifier}"

    def _get_ttl(self, prefix: str, custom_ttl: Optional[int] = None) -> int:
        """TTL 값 결정"""
        return custom_ttl or self.DEFAULT_TTL.get(prefix, 300)

    # 요금제 캐싱
    def cache_plan(self, plan_id: int, plan_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """요금제 데이터 캐싱"""
        key = self._get_key("plan", str(plan_id))
        ttl = self._get_ttl("plan", ttl)
        return self.client.set(key, plan_data, ttl)

    def get_cached_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """캐시된 요금제 데이터 조회"""
        key = self._get_key("plan", str(plan_id))
        return self.client.get(key)

    def cache_plans_list(
        self, category: Optional[str] = None, plans_data: List[Dict[str, Any]] = None, ttl: Optional[int] = None
    ) -> bool:
        """요금제 목록 캐싱"""
        key = self._get_key("plan", f"list:{category or 'all'}")
        ttl = self._get_ttl("plan", ttl)
        return self.client.set(key, plans_data, ttl)

    def get_cached_plans_list(self, category: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """캐시된 요금제 목록 조회"""
        key = self._get_key("plan", f"list:{category or 'all'}")
        return self.client.get(key)

    def invalidate_plan_cache(self, plan_id: Optional[int] = None):
        """요금제 캐시 무효화"""
        if plan_id:
            # 특정 요금제 캐시 삭제
            key = self._get_key("plan", str(plan_id))
            self.client.delete(key)

        # 요금제 목록 캐시 삭제
        list_keys = self.client.keys(self._get_key("plan", "list:*"))
        if list_keys:
            self.client.delete(*list_keys)

    # 단말기 캐싱
    def cache_device(self, device_id: int, device_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """단말기 데이터 캐싱"""
        key = self._get_key("device", str(device_id))
        ttl = self._get_ttl("device", ttl)
        return self.client.set(key, device_data, ttl)

    def get_cached_device(self, device_id: int) -> Optional[Dict[str, Any]]:
        """캐시된 단말기 데이터 조회"""
        key = self._get_key("device", str(device_id))
        return self.client.get(key)

    def cache_devices_list(
        self, brand: Optional[str] = None, devices_data: List[Dict[str, Any]] = None, ttl: Optional[int] = None
    ) -> bool:
        """단말기 목록 캐싱"""
        key = self._get_key("device", f"list:{brand or 'all'}")
        ttl = self._get_ttl("device", ttl)
        return self.client.set(key, devices_data, ttl)

    def get_cached_devices_list(self, brand: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """캐시된 단말기 목록 조회"""
        key = self._get_key("device", f"list:{brand or 'all'}")
        return self.client.get(key)

    def invalidate_device_cache(self, device_id: Optional[int] = None):
        """단말기 캐시 무효화"""
        if device_id:
            key = self._get_key("device", str(device_id))
            self.client.delete(key)

        # 단말기 목록 캐시 삭제
        list_keys = self.client.keys(self._get_key("device", "list:*"))
        if list_keys:
            self.client.delete(*list_keys)

    # 번호 캐싱
    def cache_available_numbers(self, category: str, numbers_data: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """사용 가능한 번호 목록 캐싱"""
        key = self._get_key("number", f"available:{category}")
        ttl = self._get_ttl("number", ttl)
        return self.client.set(key, numbers_data, ttl)

    def get_cached_available_numbers(self, category: str) -> Optional[List[Dict[str, Any]]]:
        """캐시된 사용 가능한 번호 목록 조회"""
        key = self._get_key("number", f"available:{category}")
        return self.client.get(key)

    def cache_number_search(self, search_query: str, results: List[Dict[str, Any]], ttl: Optional[int] = None) -> bool:
        """번호 검색 결과 캐싱"""
        # 검색 쿼리를 해시화하여 키로 사용
        query_hash = hashlib.md5(search_query.encode()).hexdigest()
        key = self._get_key("search", f"number:{query_hash}")
        ttl = self._get_ttl("search", ttl)
        return self.client.set(key, results, ttl)

    def get_cached_number_search(self, search_query: str) -> Optional[List[Dict[str, Any]]]:
        """캐시된 번호 검색 결과 조회"""
        query_hash = hashlib.md5(search_query.encode()).hexdigest()
        key = self._get_key("search", f"number:{query_hash}")
        return self.client.get(key)

    def invalidate_number_cache(self):
        """번호 관련 캐시 무효화"""
        # 사용 가능한 번호 캐시 삭제
        available_keys = self.client.keys(self._get_key("number", "available:*"))
        if available_keys:
            self.client.delete(*available_keys)

        # 번호 검색 캐시 삭제
        search_keys = self.client.keys(self._get_key("search", "number:*"))
        if search_keys:
            self.client.delete(*search_keys)

    # 사용자 세션 캐싱
    def cache_user_session(self, user_id: int, session_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """사용자 세션 데이터 캐싱"""
        key = self._get_key("session", str(user_id))
        ttl = self._get_ttl("session", ttl)
        return self.client.set(key, session_data, ttl)

    def get_cached_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """캐시된 사용자 세션 조회"""
        key = self._get_key("session", str(user_id))
        return self.client.get(key)

    def invalidate_user_session(self, user_id: int):
        """사용자 세션 캐시 무효화"""
        key = self._get_key("session", str(user_id))
        self.client.delete(key)

    # 임시 데이터 캐싱 (번호 예약, 주문 임시 저장 등)
    def cache_temp_data(self, identifier: str, data: Any, ttl: Optional[int] = None) -> bool:
        """임시 데이터 캐싱"""
        key = self._get_key("temp", identifier)
        ttl = self._get_ttl("temp", ttl)
        return self.client.set(key, data, ttl)

    def get_cached_temp_data(self, identifier: str) -> Optional[Any]:
        """캐시된 임시 데이터 조회"""
        key = self._get_key("temp", identifier)
        return self.client.get(key)

    def invalidate_temp_data(self, identifier: str):
        """임시 데이터 캐시 무효화"""
        key = self._get_key("temp", identifier)
        self.client.delete(key)

    # 통계 데이터 캐싱
    def cache_stats(self, stats_type: str, stats_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """통계 데이터 캐싱"""
        key = self._get_key("stats", stats_type)
        ttl = self._get_ttl("stats", ttl)
        return self.client.set(key, stats_data, ttl)

    def get_cached_stats(self, stats_type: str) -> Optional[Dict[str, Any]]:
        """캐시된 통계 데이터 조회"""
        key = self._get_key("stats", stats_type)
        return self.client.get(key)

    def invalidate_stats_cache(self):
        """통계 캐시 무효화"""
        stats_keys = self.client.keys(self._get_key("stats", "*"))
        if stats_keys:
            self.client.delete(*stats_keys)

    # 캐시 관리
    def get_cache_info(self) -> Dict[str, Any]:
        """캐시 정보 조회"""
        if not self.client.is_connected():
            return {"status": "disconnected"}

        info = self.client.info()

        # 각 프리픽스별 키 개수 조회
        prefix_counts = {}
        for prefix_name, prefix in self.PREFIXES.items():
            keys = self.client.keys(f"{prefix}*")
            prefix_counts[prefix_name] = len(keys)

        return {
            "status": "connected",
            "redis_info": {
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            },
            "cache_counts": prefix_counts,
            "hit_ratio": self._calculate_hit_ratio(info),
        }

    def _calculate_hit_ratio(self, info: Dict[str, Any]) -> float:
        """캐시 히트율 계산"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total > 0:
            return round((hits / total) * 100, 2)
        return 0.0

    def clear_cache(self, prefix: Optional[str] = None) -> bool:
        """캐시 삭제"""
        try:
            if prefix and prefix in self.PREFIXES:
                # 특정 프리픽스의 캐시만 삭제
                keys = self.client.keys(f"{self.PREFIXES[prefix]}*")
                if keys:
                    self.client.delete(*keys)
            else:
                # 전체 캐시 삭제
                self.client.flushdb()

            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


# 캐시 데코레이터
def cached(prefix: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None):
    """캐시 데코레이터"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_service = CacheService()

            # 캐시 키 생성
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 함수명과 인자들로 키 생성
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # 캐시에서 조회
            full_key = cache_service._get_key(prefix, cache_key)
            cached_result = cache_service.client.get(full_key)

            if cached_result is not None:
                return cached_result

            # 캐시 미스 시 함수 실행
            result = func(*args, **kwargs)

            # 결과 캐싱
            ttl_value = cache_service._get_ttl(prefix, ttl)
            cache_service.client.set(full_key, result, ttl_value)

            return result

        return wrapper

    return decorator


# 전역 캐시 서비스 인스턴스
cache_service = CacheService()
