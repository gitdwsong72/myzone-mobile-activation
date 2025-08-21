"""
Redis 클라이언트 설정 및 관리
"""

import json
import logging
import pickle
from datetime import timedelta
from typing import Any, Dict, List, Optional, Union

import redis

from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 클라이언트 래퍼 클래스"""

    def __init__(self):
        self._client = None
        self._connect()

    def _connect(self):
        """Redis 연결 설정"""
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # 바이너리 데이터 지원
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=20,
            )

            # 연결 테스트
            self._client.ping()
            logger.info("Redis connection established successfully")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None

    @property
    def client(self) -> Optional[redis.Redis]:
        """Redis 클라이언트 반환"""
        if self._client is None:
            self._connect()
        return self._client

    def is_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            if self._client:
                self._client.ping()
                return True
        except Exception:
            pass
        return False

    def set(self, key: str, value: Any, ttl: Optional[int] = None, serialize: str = "json") -> bool:
        """값 저장"""
        try:
            if not self.client:
                return False

            # 직렬화
            if serialize == "json":
                serialized_value = json.dumps(value, ensure_ascii=False)
            elif serialize == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)

            # TTL 설정
            if ttl:
                return self.client.setex(key, ttl, serialized_value)
            else:
                return self.client.set(key, serialized_value)

        except Exception as e:
            logger.error(f"Failed to set Redis key {key}: {e}")
            return False

    def get(self, key: str, serialize: str = "json") -> Optional[Any]:
        """값 조회"""
        try:
            if not self.client:
                return None

            value = self.client.get(key)
            if value is None:
                return None

            # 역직렬화
            if serialize == "json":
                return json.loads(value)
            elif serialize == "pickle":
                return pickle.loads(value)
            else:
                return value.decode("utf-8") if isinstance(value, bytes) else value

        except Exception as e:
            logger.error(f"Failed to get Redis key {key}: {e}")
            return None

    def delete(self, *keys: str) -> int:
        """키 삭제"""
        try:
            if not self.client:
                return 0
            return self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Failed to delete Redis keys {keys}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            if not self.client:
                return False
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check Redis key existence {key}: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """TTL 설정"""
        try:
            if not self.client:
                return False
            return self.client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Failed to set TTL for Redis key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """TTL 조회"""
        try:
            if not self.client:
                return -1
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Failed to get TTL for Redis key {key}: {e}")
            return -1

    def keys(self, pattern: str = "*") -> List[str]:
        """패턴으로 키 검색"""
        try:
            if not self.client:
                return []
            keys = self.client.keys(pattern)
            return [key.decode("utf-8") if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"Failed to get Redis keys with pattern {pattern}: {e}")
            return []

    def flushdb(self) -> bool:
        """현재 DB의 모든 키 삭제"""
        try:
            if not self.client:
                return False
            self.client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Failed to flush Redis DB: {e}")
            return False

    def info(self) -> Dict[str, Any]:
        """Redis 서버 정보"""
        try:
            if not self.client:
                return {}
            return self.client.info()
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}

    # Hash 연산
    def hset(self, name: str, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """해시 필드 설정"""
        try:
            if not self.client:
                return False

            # 값들을 JSON으로 직렬화
            serialized_mapping = {k: json.dumps(v, ensure_ascii=False) for k, v in mapping.items()}

            result = self.client.hset(name, mapping=serialized_mapping)

            if ttl:
                self.client.expire(name, ttl)

            return bool(result)
        except Exception as e:
            logger.error(f"Failed to set Redis hash {name}: {e}")
            return False

    def hget(self, name: str, key: str) -> Optional[Any]:
        """해시 필드 조회"""
        try:
            if not self.client:
                return None

            value = self.client.hget(name, key)
            if value is None:
                return None

            return json.loads(value)
        except Exception as e:
            logger.error(f"Failed to get Redis hash field {name}.{key}: {e}")
            return None

    def hgetall(self, name: str) -> Dict[str, Any]:
        """해시 전체 조회"""
        try:
            if not self.client:
                return {}

            hash_data = self.client.hgetall(name)
            if not hash_data:
                return {}

            # 값들을 JSON으로 역직렬화
            return {k.decode("utf-8") if isinstance(k, bytes) else k: json.loads(v) for k, v in hash_data.items()}
        except Exception as e:
            logger.error(f"Failed to get Redis hash {name}: {e}")
            return {}

    def hdel(self, name: str, *keys: str) -> int:
        """해시 필드 삭제"""
        try:
            if not self.client:
                return 0
            return self.client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Failed to delete Redis hash fields {name}.{keys}: {e}")
            return 0

    # List 연산
    def lpush(self, name: str, *values: Any) -> int:
        """리스트 왼쪽에 추가"""
        try:
            if not self.client:
                return 0

            serialized_values = [json.dumps(v, ensure_ascii=False) for v in values]
            return self.client.lpush(name, *serialized_values)
        except Exception as e:
            logger.error(f"Failed to lpush to Redis list {name}: {e}")
            return 0

    def rpush(self, name: str, *values: Any) -> int:
        """리스트 오른쪽에 추가"""
        try:
            if not self.client:
                return 0

            serialized_values = [json.dumps(v, ensure_ascii=False) for v in values]
            return self.client.rpush(name, *serialized_values)
        except Exception as e:
            logger.error(f"Failed to rpush to Redis list {name}: {e}")
            return 0

    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """리스트 범위 조회"""
        try:
            if not self.client:
                return []

            values = self.client.lrange(name, start, end)
            return [json.loads(v) for v in values]
        except Exception as e:
            logger.error(f"Failed to get Redis list range {name}: {e}")
            return []

    def ltrim(self, name: str, start: int, end: int) -> bool:
        """리스트 트림"""
        try:
            if not self.client:
                return False
            return self.client.ltrim(name, start, end)
        except Exception as e:
            logger.error(f"Failed to trim Redis list {name}: {e}")
            return False


# 전역 Redis 클라이언트 인스턴스
redis_client = RedisClient()
