"""
암호화 유틸리티 모듈
AES-256 암호화를 사용하여 민감한 개인정보를 보호합니다.
"""
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """AES-256 암호화 서비스"""
    
    def __init__(self, password: Optional[str] = None):
        """
        암호화 서비스 초기화
        
        Args:
            password: 암호화 키 생성용 패스워드 (환경변수에서 가져옴)
        """
        self.password = password or os.getenv("ENCRYPTION_PASSWORD", "default-secret-key")
        self.salt = os.getenv("ENCRYPTION_SALT", "default-salt").encode()
        self._fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Fernet 암호화 객체 생성"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return Fernet(key)
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """
        데이터 암호화
        
        Args:
            data: 암호화할 데이터 (문자열 또는 바이트)
            
        Returns:
            base64로 인코딩된 암호화된 데이터
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self._fernet.encrypt(data)
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"암호화 실패: {e}")
            raise ValueError("데이터 암호화에 실패했습니다.")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        데이터 복호화
        
        Args:
            encrypted_data: base64로 인코딩된 암호화된 데이터
            
        Returns:
            복호화된 원본 데이터
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self._fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"복호화 실패: {e}")
            raise ValueError("데이터 복호화에 실패했습니다.")
    
    def mask_sensitive_data(self, data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
        """
        민감한 데이터 마스킹 처리
        
        Args:
            data: 마스킹할 데이터
            mask_char: 마스킹에 사용할 문자
            visible_chars: 뒤에서부터 보여줄 문자 수
            
        Returns:
            마스킹된 데이터
        """
        if not data or len(data) <= visible_chars:
            return mask_char * len(data) if data else ""
        
        masked_length = len(data) - visible_chars
        return mask_char * masked_length + data[-visible_chars:]
    
    def mask_phone_number(self, phone: str) -> str:
        """전화번호 마스킹 (010-****-1234 형태)"""
        if not phone:
            return ""
        
        # 하이픈 제거 후 처리
        clean_phone = phone.replace("-", "").replace(" ", "")
        if len(clean_phone) == 11:  # 010-1234-5678 형태
            return f"{clean_phone[:3]}-****-{clean_phone[-4:]}"
        elif len(clean_phone) == 10:  # 02-1234-5678 형태
            return f"{clean_phone[:2]}-****-{clean_phone[-4:]}"
        else:
            return self.mask_sensitive_data(phone, visible_chars=4)
    
    def mask_email(self, email: str) -> str:
        """이메일 마스킹 (us***@example.com 형태)"""
        if not email or "@" not in email:
            return self.mask_sensitive_data(email, visible_chars=2)
        
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[:2] + "*" * (len(local) - 2)
        
        return f"{masked_local}@{domain}"
    
    def mask_name(self, name: str) -> str:
        """이름 마스킹 (홍*동 형태)"""
        if not name:
            return ""
        
        if len(name) <= 2:
            return name[0] + "*" * (len(name) - 1)
        else:
            return name[0] + "*" * (len(name) - 2) + name[-1]


# 전역 암호화 서비스 인스턴스
encryption_service = EncryptionService()


def encrypt_personal_data(data: str) -> str:
    """개인정보 암호화 헬퍼 함수"""
    return encryption_service.encrypt(data)


def decrypt_personal_data(encrypted_data: str) -> str:
    """개인정보 복호화 헬퍼 함수"""
    return encryption_service.decrypt(encrypted_data)


def mask_personal_data(data_type: str, data: str) -> str:
    """
    개인정보 마스킹 헬퍼 함수
    
    Args:
        data_type: 데이터 타입 (phone, email, name, etc.)
        data: 마스킹할 데이터
        
    Returns:
        마스킹된 데이터
    """
    if data_type == "phone":
        return encryption_service.mask_phone_number(data)
    elif data_type == "email":
        return encryption_service.mask_email(data)
    elif data_type == "name":
        return encryption_service.mask_name(data)
    else:
        return encryption_service.mask_sensitive_data(data)