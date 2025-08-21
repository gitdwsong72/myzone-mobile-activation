"""
커스텀 예외 클래스 정의
"""


class BaseCustomException(Exception):
    """기본 커스텀 예외 클래스"""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class UserNotFoundError(BaseCustomException):
    """사용자를 찾을 수 없는 경우 예외"""

    def __init__(self, message: str = "User not found"):
        super().__init__(message, "USER_NOT_FOUND")


class DuplicateUserError(BaseCustomException):
    """중복 사용자 예외"""

    def __init__(self, message: str = "User already exists"):
        super().__init__(message, "DUPLICATE_USER")


class PlanNotFoundError(BaseCustomException):
    """요금제를 찾을 수 없는 경우 예외"""

    def __init__(self, message: str = "Plan not found"):
        super().__init__(message, "PLAN_NOT_FOUND")


class DeviceNotFoundError(BaseCustomException):
    """단말기를 찾을 수 없는 경우 예외"""

    def __init__(self, message: str = "Device not found"):
        super().__init__(message, "DEVICE_NOT_FOUND")


class NumberNotFoundError(BaseCustomException):
    """번호를 찾을 수 없는 경우 예외"""

    def __init__(self, message: str = "Number not found"):
        super().__init__(message, "NUMBER_NOT_FOUND")


class OrderNotFoundError(BaseCustomException):
    """주문을 찾을 수 없는 경우 예외"""

    def __init__(self, message: str = "Order not found"):
        super().__init__(message, "ORDER_NOT_FOUND")


class InvalidOrderStatusError(BaseCustomException):
    """잘못된 주문 상태 예외"""

    def __init__(self, message: str = "Invalid order status"):
        super().__init__(message, "INVALID_ORDER_STATUS")


class PaymentNotFoundError(BaseCustomException):
    """결제 정보를 찾을 수 없는 경우 예외"""

    def __init__(self, message: str = "Payment not found"):
        super().__init__(message, "PAYMENT_NOT_FOUND")


class PaymentFailedError(BaseCustomException):
    """결제 실패 예외"""

    def __init__(self, message: str = "Payment failed"):
        super().__init__(message, "PAYMENT_FAILED")


class AdminNotFoundError(BaseCustomException):
    """관리자를 찾을 수 없는 경우 예외"""

    def __init__(self, message: str = "Admin not found"):
        super().__init__(message, "ADMIN_NOT_FOUND")


class UnauthorizedError(BaseCustomException):
    """인증되지 않은 접근 예외"""

    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, "UNAUTHORIZED")


class ForbiddenError(BaseCustomException):
    """권한 없는 접근 예외"""

    def __init__(self, message: str = "Forbidden access"):
        super().__init__(message, "FORBIDDEN")


class ValidationError(BaseCustomException):
    """데이터 검증 실패 예외"""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


class ExternalAPIError(BaseCustomException):
    """외부 API 호출 실패 예외"""

    def __init__(self, message: str = "External API error"):
        super().__init__(message, "EXTERNAL_API_ERROR")


class DatabaseError(BaseCustomException):
    """데이터베이스 오류 예외"""

    def __init__(self, message: str = "Database error"):
        super().__init__(message, "DATABASE_ERROR")


class FileNotFoundError(BaseCustomException):
    """파일을 찾을 수 없는 경우 예외"""

    def __init__(self, message: str = "File not found"):
        super().__init__(message, "FILE_NOT_FOUND")


class InvalidFileTypeError(BaseCustomException):
    """잘못된 파일 형식 예외"""

    def __init__(self, message: str = "Invalid file type"):
        super().__init__(message, "INVALID_FILE_TYPE")


class FileSizeExceededError(BaseCustomException):
    """파일 크기 초과 예외"""

    def __init__(self, message: str = "File size exceeded"):
        super().__init__(message, "FILE_SIZE_EXCEEDED")


class RateLimitExceededError(BaseCustomException):
    """요청 한도 초과 예외"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")


class TokenExpiredError(BaseCustomException):
    """토큰 만료 예외"""

    def __init__(self, message: str = "Token expired"):
        super().__init__(message, "TOKEN_EXPIRED")


class InvalidTokenError(BaseCustomException):
    """잘못된 토큰 예외"""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, "INVALID_TOKEN")


class VerificationCodeExpiredError(BaseCustomException):
    """인증 코드 만료 예외"""

    def __init__(self, message: str = "Verification code expired"):
        super().__init__(message, "VERIFICATION_CODE_EXPIRED")


class InvalidVerificationCodeError(BaseCustomException):
    """잘못된 인증 코드 예외"""

    def __init__(self, message: str = "Invalid verification code"):
        super().__init__(message, "INVALID_VERIFICATION_CODE")


class SMSDeliveryError(BaseCustomException):
    """SMS 발송 실패 예외"""

    def __init__(self, message: str = "SMS delivery failed"):
        super().__init__(message, "SMS_DELIVERY_ERROR")


class EmailDeliveryError(BaseCustomException):
    """이메일 발송 실패 예외"""

    def __init__(self, message: str = "Email delivery failed"):
        super().__init__(message, "EMAIL_DELIVERY_ERROR")


class InsufficientStockError(BaseCustomException):
    """재고 부족 예외"""

    def __init__(self, message: str = "Insufficient stock"):
        super().__init__(message, "INSUFFICIENT_STOCK")


class NumberReservationExpiredError(BaseCustomException):
    """번호 예약 만료 예외"""

    def __init__(self, message: str = "Number reservation expired"):
        super().__init__(message, "NUMBER_RESERVATION_EXPIRED")


class NumberAlreadyReservedError(BaseCustomException):
    """번호 이미 예약됨 예외"""

    def __init__(self, message: str = "Number already reserved"):
        super().__init__(message, "NUMBER_ALREADY_RESERVED")


class ConfigurationError(BaseCustomException):
    """설정 오류 예외"""

    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, "CONFIGURATION_ERROR")


class ServiceUnavailableError(BaseCustomException):
    """서비스 사용 불가 예외"""

    def __init__(self, message: str = "Service unavailable"):
        super().__init__(message, "SERVICE_UNAVAILABLE")
