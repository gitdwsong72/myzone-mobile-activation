"""
보안 유틸리티 함수들
입력 검증, 데이터 새니타이징, 보안 검사 등
"""

import hashlib
import html
import ipaddress
import logging
import re
import secrets
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class InputValidator:
    """입력 데이터 검증 클래스"""

    # 정규식 패턴들
    PATTERNS = {
        "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
        "phone": re.compile(r"^01[0-9]-\d{3,4}-\d{4}$"),
        "korean_name": re.compile(r"^[가-힣]{2,10}$"),
        "english_name": re.compile(r"^[a-zA-Z\s]{2,50}$"),
        "password": re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"),
        "alphanumeric": re.compile(r"^[a-zA-Z0-9]+$"),
        "numeric": re.compile(r"^\d+$"),
        "url": re.compile(r"^https?://[^\s/$.?#].[^\s]*$"),
    }

    # 위험한 패턴들
    DANGEROUS_PATTERNS = {
        "sql_injection": re.compile(
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b)|"
            r"(--|#|/\*|\*/)|"
            r"(\bxp_cmdshell\b)|"
            r"(\bsp_executesql\b)",
            re.IGNORECASE,
        ),
        "xss": re.compile(
            r"<script[^>]*>.*?</script>|" r"javascript:|vbscript:|" r"on\w+\s*=|" r"eval\s*\(|" r"expression\s*\(",
            re.IGNORECASE,
        ),
        "path_traversal": re.compile(r"\.\.[\\/]"),
        "command_injection": re.compile(
            r"[;&|`$(){}[\]<>]|" r"\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig|ping|wget|curl)\b", re.IGNORECASE
        ),
    }

    @classmethod
    def validate_email(cls, email: str) -> bool:
        """이메일 주소 검증"""
        if not email or len(email) > 254:
            return False
        return bool(cls.PATTERNS["email"].match(email))

    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        """전화번호 검증"""
        if not phone:
            return False
        # 하이픈 제거 후 검증
        clean_phone = phone.replace("-", "").replace(" ", "")
        if len(clean_phone) != 11 or not clean_phone.startswith("01"):
            return False
        return clean_phone.isdigit()

    @classmethod
    def validate_korean_name(cls, name: str) -> bool:
        """한국어 이름 검증"""
        if not name or len(name) < 2 or len(name) > 10:
            return False
        return bool(cls.PATTERNS["korean_name"].match(name))

    @classmethod
    def validate_password(cls, password: str) -> bool:
        """비밀번호 강도 검증"""
        if not password or len(password) < 8 or len(password) > 128:
            return False
        return bool(cls.PATTERNS["password"].match(password))

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """URL 검증"""
        if not url:
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ["http", "https"]
        except Exception:
            return False

    @classmethod
    def is_safe_string(cls, text: str) -> bool:
        """문자열이 안전한지 검증"""
        if not text:
            return True

        for pattern_name, pattern in cls.DANGEROUS_PATTERNS.items():
            if pattern.search(text):
                logger.warning(f"Dangerous pattern detected: {pattern_name} in text: {text[:100]}")
                return False

        return True

    @classmethod
    def validate_file_extension(cls, filename: str, allowed_extensions: List[str]) -> bool:
        """파일 확장자 검증"""
        if not filename or "." not in filename:
            return False

        extension = filename.rsplit(".", 1)[1].lower()
        return extension in [ext.lower() for ext in allowed_extensions]

    @classmethod
    def validate_file_size(cls, file_size: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """파일 크기 검증 (기본 10MB)"""
        return 0 < file_size <= max_size

    @classmethod
    def validate_ip_address(cls, ip: str) -> bool:
        """IP 주소 검증"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False


class DataSanitizer:
    """데이터 새니타이징 클래스"""

    @staticmethod
    def sanitize_html(text: str) -> str:
        """HTML 새니타이징"""
        if not text:
            return ""
        return html.escape(text)

    @staticmethod
    def sanitize_sql(text: str) -> str:
        """SQL 새니타이징 (기본적인 이스케이프)"""
        if not text:
            return ""
        # 작은따옴표 이스케이프
        return text.replace("'", "''")

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """파일명 새니타이징"""
        if not filename:
            return ""

        # 위험한 문자 제거
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(dangerous_chars, "_", filename)

        # 예약된 이름 확인 (Windows)
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }

        name_without_ext = sanitized.rsplit(".", 1)[0] if "." in sanitized else sanitized
        if name_without_ext.upper() in reserved_names:
            sanitized = f"_{sanitized}"

        # 길이 제한
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
            max_name_len = 255 - len(ext) - 1 if ext else 255
            sanitized = f"{name[:max_name_len]}.{ext}" if ext else name[:255]

        return sanitized

    @staticmethod
    def sanitize_json_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """JSON 입력 데이터 새니타이징"""
        if not isinstance(data, dict):
            return {}

        sanitized = {}
        for key, value in data.items():
            # 키 새니타이징
            clean_key = DataSanitizer.sanitize_html(str(key))

            # 값 새니타이징
            if isinstance(value, str):
                clean_value = DataSanitizer.sanitize_html(value)
            elif isinstance(value, dict):
                clean_value = DataSanitizer.sanitize_json_input(value)
            elif isinstance(value, list):
                clean_value = [DataSanitizer.sanitize_html(str(item)) if isinstance(item, str) else item for item in value]
            else:
                clean_value = value

            sanitized[clean_key] = clean_value

        return sanitized


class SecurityChecker:
    """보안 검사 클래스"""

    @staticmethod
    def check_password_strength(password: str) -> Dict[str, Any]:
        """비밀번호 강도 검사"""
        if not password:
            return {"score": 0, "feedback": ["비밀번호를 입력해주세요."]}

        score = 0
        feedback = []

        # 길이 검사
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("8자 이상이어야 합니다.")

        # 대문자 포함
        if re.search(r"[A-Z]", password):
            score += 1
        else:
            feedback.append("대문자를 포함해야 합니다.")

        # 소문자 포함
        if re.search(r"[a-z]", password):
            score += 1
        else:
            feedback.append("소문자를 포함해야 합니다.")

        # 숫자 포함
        if re.search(r"\d", password):
            score += 1
        else:
            feedback.append("숫자를 포함해야 합니다.")

        # 특수문자 포함
        if re.search(r"[@$!%*?&]", password):
            score += 1
        else:
            feedback.append("특수문자(@$!%*?&)를 포함해야 합니다.")

        # 연속된 문자 검사
        if not re.search(r"(.)\1{2,}", password):
            score += 1
        else:
            feedback.append("동일한 문자가 3번 이상 연속되면 안됩니다.")

        return {
            "score": score,
            "max_score": 6,
            "strength": SecurityChecker._get_password_strength_label(score),
            "feedback": feedback,
        }

    @staticmethod
    def _get_password_strength_label(score: int) -> str:
        """비밀번호 강도 라벨"""
        if score <= 2:
            return "매우 약함"
        elif score <= 3:
            return "약함"
        elif score <= 4:
            return "보통"
        elif score <= 5:
            return "강함"
        else:
            return "매우 강함"

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """보안 토큰 생성"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_csrf_token() -> str:
        """CSRF 토큰 생성"""
        return secrets.token_hex(16)

    @staticmethod
    def hash_data(data: str, salt: Optional[str] = None) -> str:
        """데이터 해싱"""
        if salt is None:
            salt = secrets.token_hex(16)

        hash_obj = hashlib.sha256()
        hash_obj.update((data + salt).encode("utf-8"))
        return f"{salt}:{hash_obj.hexdigest()}"

    @staticmethod
    def verify_hash(data: str, hashed: str) -> bool:
        """해시 검증"""
        try:
            salt, hash_value = hashed.split(":", 1)
            hash_obj = hashlib.sha256()
            hash_obj.update((data + salt).encode("utf-8"))
            return hash_obj.hexdigest() == hash_value
        except ValueError:
            return False

    @staticmethod
    def is_suspicious_user_agent(user_agent: str) -> bool:
        """의심스러운 User-Agent 검사"""
        if not user_agent or len(user_agent) < 10:
            return True

        # 알려진 봇/크롤러 패턴
        suspicious_patterns = [
            r"bot",
            r"crawler",
            r"spider",
            r"scraper",
            r"curl",
            r"wget",
            r"python",
            r"java",
            r"go-http-client",
        ]

        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent_lower):
                return True

        return False

    @staticmethod
    def check_request_anomaly(request_data: Dict[str, Any]) -> List[str]:
        """요청 이상 징후 검사"""
        anomalies = []

        # 요청 크기 검사
        if request_data.get("content_length", 0) > 10 * 1024 * 1024:  # 10MB
            anomalies.append("Request size too large")

        # 헤더 수 검사
        headers_count = len(request_data.get("headers", {}))
        if headers_count > 50:
            anomalies.append("Too many headers")

        # User-Agent 검사
        user_agent = request_data.get("user_agent", "")
        if SecurityChecker.is_suspicious_user_agent(user_agent):
            anomalies.append("Suspicious User-Agent")

        # 요청 빈도 검사 (여기서는 기본적인 검사만)
        # 실제로는 Redis나 다른 저장소를 사용해야 함

        return anomalies


class CSRFProtection:
    """CSRF 보호 클래스"""

    @staticmethod
    def generate_token(session_id: str) -> str:
        """CSRF 토큰 생성"""
        timestamp = str(int(time.time()))
        data = f"{session_id}:{timestamp}"
        return SecurityChecker.hash_data(data)

    @staticmethod
    def validate_token(token: str, session_id: str, max_age: int = 3600) -> bool:
        """CSRF 토큰 검증"""
        try:
            import time

            current_time = int(time.time())

            # 토큰에서 타임스탬프 추출
            salt, hash_value = token.split(":", 1)

            # 가능한 타임스탬프들을 확인 (max_age 범위 내)
            for i in range(max_age):
                timestamp = str(current_time - i)
                data = f"{session_id}:{timestamp}"
                expected_token = SecurityChecker.hash_data(data, salt)

                if expected_token == token:
                    return True

            return False
        except Exception:
            return False
