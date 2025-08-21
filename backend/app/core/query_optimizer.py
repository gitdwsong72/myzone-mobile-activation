"""
쿼리 성능 최적화 유틸리티
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """쿼리 성능 최적화 및 분석 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_query_performance(self, query: str, params: Dict = None) -> Dict[str, Any]:
        """쿼리 성능 분석"""
        try:
            # EXPLAIN ANALYZE 실행
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            result = self.db.execute(text(explain_query), params or {})

            analysis = result.fetchone()[0][0]

            return {
                "execution_time": analysis.get("Execution Time", 0),
                "planning_time": analysis.get("Planning Time", 0),
                "total_cost": analysis.get("Plan", {}).get("Total Cost", 0),
                "rows": analysis.get("Plan", {}).get("Actual Rows", 0),
                "analysis": analysis,
            }
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {"error": str(e)}

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """느린 쿼리 조회 (PostgreSQL pg_stat_statements 확장 필요)"""
        try:
            query = text(
                """
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE query NOT LIKE '%pg_stat_statements%'
                ORDER BY mean_exec_time DESC 
                LIMIT :limit
            """
            )

            result = self.db.execute(query, {"limit": limit})
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not fetch slow queries: {e}")
            return []

    def get_index_usage_stats(self) -> List[Dict[str, Any]]:
        """인덱스 사용 통계 조회"""
        try:
            query = text(
                """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan,
                    CASE 
                        WHEN idx_scan = 0 THEN 'Unused'
                        WHEN idx_scan < 10 THEN 'Low Usage'
                        ELSE 'Active'
                    END as usage_status
                FROM pg_stat_user_indexes 
                ORDER BY idx_scan DESC
            """
            )

            result = self.db.execute(query)
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not fetch index stats: {e}")
            return []

    def get_table_stats(self) -> List[Dict[str, Any]]:
        """테이블 통계 조회"""
        try:
            query = text(
                """
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_tup_hot_upd as hot_updates,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables 
                ORDER BY n_live_tup DESC
            """
            )

            result = self.db.execute(query)
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not fetch table stats: {e}")
            return []

    def optimize_query_hints(self, base_query: str, table_name: str) -> str:
        """쿼리 힌트 추가로 성능 최적화"""
        hints = {
            "users": "/*+ USE_INDEX(users, idx_users_phone) */",
            "orders": "/*+ USE_INDEX(orders, idx_orders_status_created_at) */",
            "plans": "/*+ USE_INDEX(plans, idx_plans_active_category_order) */",
            "devices": "/*+ USE_INDEX(devices, idx_devices_active_brand_price) */",
            "numbers": "/*+ USE_INDEX(numbers, idx_numbers_category_status_fee) */",
        }

        hint = hints.get(table_name, "")
        if hint:
            return f"{hint}\n{base_query}"
        return base_query

    def suggest_indexes(self, table_name: str, where_columns: List[str], order_columns: List[str] = None) -> List[str]:
        """인덱스 제안"""
        suggestions = []

        if len(where_columns) == 1:
            suggestions.append(f"CREATE INDEX idx_{table_name}_{where_columns[0]} ON {table_name} ({where_columns[0]})")
        elif len(where_columns) > 1:
            col_str = "_".join(where_columns)
            suggestions.append(f"CREATE INDEX idx_{table_name}_{col_str} ON {table_name} ({', '.join(where_columns)})")

        if order_columns:
            all_columns = where_columns + order_columns
            col_str = "_".join(all_columns)
            suggestions.append(f"CREATE INDEX idx_{table_name}_{col_str} ON {table_name} ({', '.join(all_columns)})")

        return suggestions


class QueryCache:
    """쿼리 결과 캐싱 클래스"""

    def __init__(self):
        self._cache = {}
        self._cache_ttl = {}

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key in self._cache:
            if datetime.now() < self._cache_ttl.get(key, datetime.min):
                return self._cache[key]
            else:
                # TTL 만료된 캐시 삭제
                del self._cache[key]
                if key in self._cache_ttl:
                    del self._cache_ttl[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """캐시에 값 저장"""
        self._cache[key] = value
        self._cache_ttl[key] = datetime.now() + timedelta(seconds=ttl_seconds)

    def clear(self):
        """캐시 전체 삭제"""
        self._cache.clear()
        self._cache_ttl.clear()

    def get_stats(self) -> Dict[str, int]:
        """캐시 통계"""
        now = datetime.now()
        valid_keys = sum(1 for ttl in self._cache_ttl.values() if now < ttl)

        return {"total_keys": len(self._cache), "valid_keys": valid_keys, "expired_keys": len(self._cache) - valid_keys}


# 전역 쿼리 캐시 인스턴스
query_cache = QueryCache()


def cached_query(cache_key: str, ttl_seconds: int = 300):
    """쿼리 결과 캐싱 데코레이터"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # 캐시에서 조회
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 캐시 미스 시 실제 쿼리 실행
            result = func(*args, **kwargs)

            # 결과 캐싱
            query_cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper

    return decorator


def get_optimized_pagination(page: int, size: int, max_size: int = 100) -> tuple:
    """최적화된 페이지네이션 파라미터"""
    page = max(1, page)
    size = min(max(1, size), max_size)
    offset = (page - 1) * size

    return offset, size
