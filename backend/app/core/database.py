from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from app.core.config import settings
import logging
import time

# 로거 설정
logger = logging.getLogger(__name__)

# 데이터베이스 엔진 생성 (성능 최적화된 설정)
engine = create_engine(
    settings.DATABASE_URL,
    # 커넥션 풀 설정
    pool_pre_ping=True,          # 커넥션 유효성 검사
    pool_recycle=3600,           # 1시간마다 커넥션 재생성
    pool_size=20,                # 기본 커넥션 풀 크기 증가
    max_overflow=30,             # 최대 오버플로우 커넥션 수 증가
    pool_timeout=30,             # 커넥션 대기 시간
    
    # 성능 최적화 설정
    echo=False,                  # SQL 로깅 비활성화 (프로덕션)
    echo_pool=False,             # 풀 로깅 비활성화
    future=True,                 # SQLAlchemy 2.0 스타일 사용
    
    # PostgreSQL 특화 설정
    connect_args={
        "options": "-c timezone=Asia/Seoul",
        "application_name": "myzone_backend",
        "connect_timeout": 10,
    }
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # 성능 향상을 위해 비활성화
)

# Base 클래스 생성
Base = declarative_base()


# 쿼리 성능 모니터링 이벤트 리스너
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """쿼리 실행 전 시간 기록"""
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """쿼리 실행 후 성능 로깅"""
    total = time.time() - context._query_start_time
    
    # 느린 쿼리 로깅 (1초 이상)
    if total > 1.0:
        logger.warning(
            f"Slow query detected: {total:.2f}s - {statement[:200]}..."
        )
    
    # 매우 느린 쿼리 로깅 (5초 이상)
    if total > 5.0:
        logger.error(
            f"Very slow query detected: {total:.2f}s - {statement[:200]}..."
        )


# 데이터베이스 세션 의존성
def get_db():
    """데이터베이스 세션 생성 및 관리"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# 데이터베이스 연결 상태 확인
def check_db_connection():
    """데이터베이스 연결 상태 확인"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# 커넥션 풀 상태 조회
def get_pool_status():
    """커넥션 풀 상태 정보 반환"""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid()
    }