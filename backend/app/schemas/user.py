"""
사용자 관련 Pydantic 스키마
"""
from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, Dict, Any
from datetime import date, datetime
import re


class UserBase(BaseModel):
    """사용자 기본 정보"""
    name: str = Field(..., min_length=2, max_length=50, description="사용자 이름")
    phone: str = Field(..., description="휴대폰 번호")
    email: Optional[EmailStr] = Field(None, description="이메일 주소")
    birth_date: date = Field(..., description="생년월일")
    gender: str = Field(..., description="성별 (M/F)")
    address: str = Field(..., min_length=10, max_length=500, description="주소")
    
    @validator('phone')
    def validate_phone(cls, v):
        """전화번호 형식 검증"""
        # 하이픈 제거 후 검증
        clean_phone = re.sub(r'[^0-9]', '', v)
        
        # 휴대폰 번호 패턴 (010, 011, 016, 017, 018, 019)
        if not re.match(r'^01[0-9]\d{7,8}$', clean_phone):
            raise ValueError('올바른 휴대폰 번호 형식이 아닙니다.')
        
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        """성별 검증"""
        if v.upper() not in ['M', 'F', 'MALE', 'FEMALE']:
            raise ValueError('성별은 M, F, MALE, FEMALE 중 하나여야 합니다.')
        return v.upper()
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        """생년월일 검증"""
        from datetime import date
        today = date.today()
        
        # 미래 날짜 불가
        if v > today:
            raise ValueError('생년월일은 미래 날짜일 수 없습니다.')
        
        # 만 14세 이상만 가입 가능
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 14:
            raise ValueError('만 14세 이상만 가입 가능합니다.')
        
        return v


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    verification_method: Optional[str] = Field(None, description="본인인증 방법")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "홍길동",
                "phone": "010-1234-5678",
                "email": "hong@example.com",
                "birth_date": "1990-01-01",
                "gender": "M",
                "address": "서울특별시 강남구 테헤란로 123",
                "verification_method": "SMS"
            }
        }


class UserUpdate(BaseModel):
    """사용자 정보 수정 스키마"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    
    class Config:
        schema_extra = {
            "example": {
                "name": "홍길동",
                "email": "newemail@example.com",
                "address": "서울특별시 서초구 서초대로 456"
            }
        }


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int
    name: str
    phone: str
    email: Optional[str]
    birth_date: date
    gender: str
    address: str
    is_verified: bool
    verification_method: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserMaskedResponse(BaseModel):
    """마스킹된 사용자 응답 스키마 (민감정보 보호)"""
    id: int
    name: str  # 마스킹됨
    phone: str  # 마스킹됨
    email: Optional[str]  # 마스킹됨
    birth_date: date
    gender: str
    address: str  # 일부 마스킹됨
    is_verified: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AddressSearchRequest(BaseModel):
    """주소 검색 요청 스키마"""
    keyword: str = Field(..., min_length=2, max_length=100, description="검색 키워드")
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(10, ge=1, le=50, description="페이지 크기")
    
    class Config:
        schema_extra = {
            "example": {
                "keyword": "테헤란로",
                "page": 1,
                "size": 10
            }
        }


class AddressSearchResponse(BaseModel):
    """주소 검색 응답 스키마"""
    success: bool
    data: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "addresses": [
                        {
                            "zipcode": "06234",
                            "address": "서울특별시 강남구 테헤란로",
                            "detail": "123 (역삼동)"
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "size": 10
                }
            }
        }


class UserVerificationRequest(BaseModel):
    """본인인증 요청 스키마"""
    method: str = Field(..., description="인증 방법 (SMS, CERTIFICATE, SIMPLE)")
    phone: Optional[str] = Field(None, description="SMS 인증용 전화번호")
    
    @validator('method')
    def validate_method(cls, v):
        """인증 방법 검증"""
        allowed_methods = ['SMS', 'CERTIFICATE', 'SIMPLE']
        if v.upper() not in allowed_methods:
            raise ValueError(f'인증 방법은 {", ".join(allowed_methods)} 중 하나여야 합니다.')
        return v.upper()
    
    class Config:
        schema_extra = {
            "example": {
                "method": "SMS",
                "phone": "010-1234-5678"
            }
        }


class UserVerificationResponse(BaseModel):
    """본인인증 응답 스키마"""
    success: bool
    message: str
    verification_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "인증번호가 발송되었습니다.",
                "verification_id": "verify_123456",
                "expires_at": "2024-01-01T12:05:00"
            }
        }


class UserVerificationConfirmRequest(BaseModel):
    """본인인증 확인 요청 스키마"""
    verification_id: str = Field(..., description="인증 ID")
    code: str = Field(..., min_length=4, max_length=6, description="인증번호")
    
    class Config:
        schema_extra = {
            "example": {
                "verification_id": "verify_123456",
                "code": "123456"
            }
        }


class UserDeletionRequest(BaseModel):
    """사용자 계정 삭제 요청 스키마"""
    reason: Optional[str] = Field(None, max_length=500, description="삭제 사유")
    confirm: bool = Field(..., description="삭제 확인")
    
    @validator('confirm')
    def validate_confirm(cls, v):
        """삭제 확인 검증"""
        if not v:
            raise ValueError('계정 삭제를 확인해주세요.')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "reason": "서비스 이용 중단",
                "confirm": True
            }
        }