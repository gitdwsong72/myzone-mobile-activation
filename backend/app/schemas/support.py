from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class FAQBase(BaseModel):
    category: str
    question: str
    answer: str


class FAQCreate(FAQBase):
    is_active: bool = True


class FAQUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    is_active: Optional[bool] = None


class FAQResponse(FAQBase):
    id: int
    is_active: bool
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FAQListResponse(BaseModel):
    faqs: List[FAQResponse]
    total: int
    categories: List[str]


class InquiryBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    order_number: Optional[str] = None
    category: str
    subject: str
    content: str


class InquiryCreate(InquiryBase):
    pass


class InquiryUpdate(BaseModel):
    status: Optional[str] = None
    admin_reply: Optional[str] = None


class InquiryResponse(InquiryBase):
    id: int
    status: str
    admin_reply: Optional[str] = None
    replied_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InquiryListResponse(BaseModel):
    inquiries: List[InquiryResponse]
    total: int
    page: int
    size: int
    total_pages: int
