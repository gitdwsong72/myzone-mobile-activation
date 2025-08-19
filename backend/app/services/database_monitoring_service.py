"""
데이터베이스 성능 모니터링 서비스
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from ..core.query_optimizer import QueryOptimizer
from ..core.database import get_pool_status, check_db_connection

logger = logging.getLogger(__name__)


class DatabaseMonitoringService:
    """데이터베이스 성능 모니터링 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.optimizer = QueryOptimizer(db)
    
    def get_database_health(self) -> Dict[str, Any]:
        """데이터베이스 전반적인 상태 조회"""
        try:
            health_data = {
                "connection_status": check_db_connection(),
                "pool_status": get_pool_status(),
                "active_connections": self._get_active_connections(),
                "database_size": self._get_database_size(),
                "table_sizes": self._get_table_sizes(),
                "index_usage": self._get_index_efficiency(),
                "slow_queries": self.optimizer.get_slow_queries(5),
                "timestamp": datetime.now().isoformat()
            }
            
            return health_data
        except Exception as e:
            logger.error(f"Failed to get database health: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def _get_active_connections(self) -> Dict[str, Any]:
        """활성 연결 수 조회"""
        try:
            query = text("""
                SELECT 
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            result = self.db.execute(query).fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.warning(f"Could not get connection stats: {e}")
            return {}
    
    def _get_database_size(self) -> Dict[str, Any]:
        """데이터베이스 크기 조회"""
        try:
            query = text("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    pg_database_size(current_database()) as database_size_bytes
            """)
            
            result = self.db.execute(query).fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.warning(f"Could not get database size: {e}")
            return {}
    
    def _get_table_sizes(self) -> List[Dict[str, Any]]:
        """테이블별 크기 조회"""
        try:
            query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_size_bytes,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                    pg_relation_size(schemaname||'.'||tablename) as table_size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)
            
            result = self.db.execute(query)
            return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.warning(f"Could not get table sizes: {e}")
            return []
    
    def _get_index_efficiency(self) -> Dict[str, Any]:
        """인덱스 효율성 분석"""
        try:
            # 전체 인덱스 사용률
            usage_query = text("""
                SELECT 
                    count(*) as total_indexes,
                    count(*) FILTER (WHERE idx_scan > 0) as used_indexes,
                    count(*) FILTER (WHERE idx_scan = 0) as unused_indexes,
                    round(avg(idx_scan), 2) as avg_scans
                FROM pg_stat_user_indexes
            """)
            
            usage_result = self.db.execute(usage_query).fetchone()
            usage_stats = dict(usage_result) if usage_result else {}
            
            # 사용되지 않는 인덱스 목록
            unused_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes 
                WHERE idx_scan = 0
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 5
            """)
            
            unused_result = self.db.execute(unused_query)
            unused_indexes = [dict(row) for row in unused_result.fetchall()]
            
            return {
                "usage_stats": usage_stats,
                "unused_indexes": unused_indexes
            }
        except Exception as e:
            logger.warning(f"Could not get index efficiency: {e}")
            return {}
    
    def get_query_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """쿼리 성능 리포트 생성"""
        try:
            # 최근 N시간 동안의 쿼리 통계
            stats_query = text("""
                SELECT 
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    min_exec_time,
                    stddev_exec_time,
                    rows,
                    shared_blks_hit,
                    shared_blks_read,
                    shared_blks_dirtied,
                    shared_blks_written,
                    temp_blks_read,
                    temp_blks_written
                FROM pg_stat_statements
                WHERE last_exec > NOW() - INTERVAL ':hours hours'
            """)
            
            result = self.db.execute(stats_query, {"hours": hours})
            stats = [dict(row) for row in result.fetchall()]
            
            if not stats:
                return {"message": "No query statistics available"}
            
            # 통계 계산
            total_calls = sum(s['calls'] for s in stats)
            total_time = sum(s['total_exec_time'] for s in stats)
            avg_time = total_time / total_calls if total_calls > 0 else 0
            
            return {
                "period_hours": hours,
                "total_queries": total_calls,
                "total_execution_time_ms": round(total_time, 2),
                "average_execution_time_ms": round(avg_time, 2),
                "slowest_queries": self.optimizer.get_slow_queries(10),
                "cache_hit_ratio": self._calculate_cache_hit_ratio(stats),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}
    
    def _calculate_cache_hit_ratio(self, stats: List[Dict]) -> float:
        """캐시 히트율 계산"""
        try:
            total_hits = sum(s['shared_blks_hit'] for s in stats)
            total_reads = sum(s['shared_blks_read'] for s in stats)
            total_access = total_hits + total_reads
            
            if total_access > 0:
                return round((total_hits / total_access) * 100, 2)
            return 0.0
        except Exception:
            return 0.0
    
    def get_maintenance_recommendations(self) -> List[Dict[str, Any]]:
        """데이터베이스 유지보수 권장사항"""
        recommendations = []
        
        try:
            # 오래된 통계 정보 확인
            stats_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    last_analyze,
                    last_autoanalyze,
                    n_dead_tup,
                    n_live_tup
                FROM pg_stat_user_tables
                WHERE last_analyze < NOW() - INTERVAL '7 days'
                   OR last_autoanalyze < NOW() - INTERVAL '7 days'
                   OR (n_dead_tup > 0 AND n_dead_tup::float / NULLIF(n_live_tup, 0) > 0.1)
            """)
            
            result = self.db.execute(stats_query)
            stale_stats = [dict(row) for row in result.fetchall()]
            
            for table in stale_stats:
                if table['last_analyze'] and table['last_analyze'] < datetime.now() - timedelta(days=7):
                    recommendations.append({
                        "type": "analyze",
                        "priority": "medium",
                        "table": f"{table['schemaname']}.{table['tablename']}",
                        "description": f"테이블 {table['tablename']}의 통계 정보가 오래되었습니다. ANALYZE를 실행하세요.",
                        "command": f"ANALYZE {table['schemaname']}.{table['tablename']};"
                    })
                
                dead_ratio = table['n_dead_tup'] / max(table['n_live_tup'], 1) if table['n_live_tup'] else 0
                if dead_ratio > 0.1:
                    recommendations.append({
                        "type": "vacuum",
                        "priority": "high" if dead_ratio > 0.3 else "medium",
                        "table": f"{table['schemaname']}.{table['tablename']}",
                        "description": f"테이블 {table['tablename']}에 죽은 튜플이 많습니다 ({dead_ratio:.1%}). VACUUM을 실행하세요.",
                        "command": f"VACUUM ANALYZE {table['schemaname']}.{table['tablename']};"
                    })
            
            # 사용되지 않는 인덱스 확인
            unused_indexes = self.optimizer.get_index_usage_stats()
            for index in unused_indexes:
                if index.get('usage_status') == 'Unused':
                    recommendations.append({
                        "type": "index_cleanup",
                        "priority": "low",
                        "table": f"{index['schemaname']}.{index['tablename']}",
                        "description": f"인덱스 {index['indexname']}가 사용되지 않고 있습니다. 삭제를 고려하세요.",
                        "command": f"DROP INDEX IF EXISTS {index['indexname']};"
                    })
            
        except Exception as e:
            logger.error(f"Failed to generate maintenance recommendations: {e}")
            recommendations.append({
                "type": "error",
                "priority": "high",
                "description": f"유지보수 권장사항 생성 중 오류 발생: {e}"
            })
        
        return recommendations
    
    def run_maintenance_task(self, task_type: str, table_name: str = None) -> Dict[str, Any]:
        """유지보수 작업 실행"""
        try:
            if task_type == "analyze":
                if table_name:
                    self.db.execute(text(f"ANALYZE {table_name}"))
                else:
                    self.db.execute(text("ANALYZE"))
                
                return {"status": "success", "message": f"ANALYZE 완료: {table_name or 'all tables'}"}
            
            elif task_type == "vacuum":
                if table_name:
                    self.db.execute(text(f"VACUUM ANALYZE {table_name}"))
                else:
                    self.db.execute(text("VACUUM ANALYZE"))
                
                return {"status": "success", "message": f"VACUUM 완료: {table_name or 'all tables'}"}
            
            elif task_type == "reindex":
                if table_name:
                    self.db.execute(text(f"REINDEX TABLE {table_name}"))
                else:
                    self.db.execute(text("REINDEX DATABASE CONCURRENTLY"))
                
                return {"status": "success", "message": f"REINDEX 완료: {table_name or 'database'}"}
            
            else:
                return {"status": "error", "message": f"알 수 없는 작업 유형: {task_type}"}
        
        except Exception as e:
            logger.error(f"Maintenance task failed: {e}")
            return {"status": "error", "message": str(e)}