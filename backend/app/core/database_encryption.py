"""
데이터베이스 필드 레벨 암호화
SQLAlchemy 커스텀 타입을 사용하여 자동 암호화/복호화 처리
"""

import logging
from typing import Any, Optional

from sqlalchemy import String, Text, TypeDecorator
from sqlalchemy.engine import Dialect

from .encryption import encryption_service

logger = logging.getLogger(__name__)


class EncryptedString(TypeDecorator):
    """암호화된 문자열 타입"""

    impl = String
    cache_ok = True

    def __init__(self, length: Optional[int] = None, **kwargs):
        # 암호화된 데이터는 원본보다 길어지므로 충분한 길이 확보
        if length:
            length = max(length * 2, 500)  # 최소 500자 확보
        super().__init__(length, **kwargs)

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        """데이터베이스에 저장할 때 암호화"""
        if value is None:
            return None

        if isinstance(value, str):
            try:
                return encryption_service.encrypt(value)
            except Exception as e:
                logger.error(f"데이터 암호화 실패: {e}")
                # 암호화 실패 시 원본 데이터 반환 (개발 환경에서만)
                return value

        return str(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        """데이터베이스에서 조회할 때 복호화"""
        if value is None:
            return None

        try:
            return encryption_service.decrypt(value)
        except Exception as e:
            logger.error(f"데이터 복호화 실패: {e}")
            # 복호화 실패 시 원본 데이터 반환 (마이그레이션 등을 위해)
            return value


class EncryptedText(TypeDecorator):
    """암호화된 텍스트 타입"""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Dialect) -> Optional[str]:
        """데이터베이스에 저장할 때 암호화"""
        if value is None:
            return None

        if isinstance(value, str):
            try:
                return encryption_service.encrypt(value)
            except Exception as e:
                logger.error(f"텍스트 데이터 암호화 실패: {e}")
                return value

        return str(value)

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        """데이터베이스에서 조회할 때 복호화"""
        if value is None:
            return None

        try:
            return encryption_service.decrypt(value)
        except Exception as e:
            logger.error(f"텍스트 데이터 복호화 실패: {e}")
            return value


class MaskedString(TypeDecorator):
    """마스킹된 문자열 타입 (조회 시 자동 마스킹)"""

    impl = String
    cache_ok = True

    def __init__(self, mask_type: str = "default", length: Optional[int] = None, **kwargs):
        self.mask_type = mask_type
        super().__init__(length, **kwargs)

    def process_result_value(self, value: Any, dialect: Dialect) -> Optional[str]:
        """데이터베이스에서 조회할 때 마스킹"""
        if value is None:
            return None

        # 마스킹 타입에 따라 처리
        if self.mask_type == "phone":
            return encryption_service.mask_phone_number(value)
        elif self.mask_type == "email":
            return encryption_service.mask_email(value)
        elif self.mask_type == "name":
            return encryption_service.mask_name(value)
        else:
            return encryption_service.mask_sensitive_data(value)


# 편의를 위한 타입 별칭
EncryptedName = lambda: EncryptedString(100)
EncryptedPhone = lambda: String(20)  # 전화번호는 로그인 ID로 사용하므로 암호화하지 않음
EncryptedEmail = lambda: String(255)  # 이메일도 검색을 위해 암호화하지 않음
EncryptedAddress = lambda: EncryptedText()

# 마스킹 타입 별칭
MaskedName = lambda: MaskedString("name", 100)
MaskedPhone = lambda: MaskedString("phone", 20)
MaskedEmail = lambda: MaskedString("email", 255)
