from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_admin_user
from ...services.support_service import SupportService
from ...schemas.support import (
    FAQResponse, FAQListResponse, FAQCreate, FAQUpdate,
    InquiryResponse, InquiryListResponse, InquiryCreate, InquiryUpdate
)
from ...models.admin import Admin

router = APIRouter()


def get_support_service(db: Session = Depends(get_db)) -> SupportService:
    """고객지원 서비스 의존성"""
    return SupportService(db)


# FAQ 관련 엔드포인트
@router.get("/faqs", response_model=FAQListResponse)
async def get_faqs(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    search: Optional[str] = Query(None, description="검색어"),
    support_service: SupportService = Depends(get_support_service)
):
    """
    FAQ 목록 조회
    
    - **category**: 카테고리 필터
    - **search**: 검색어 (질문, 답변 내용 검색)
    """
    return support_service.get_faqs(category=category, search=search)


@router.get("/faqs/{faq_id}", response_model=FAQResponse)
async def get_faq(
    faq_id: int,
    support_service: SupportService = Depends(get_support_service)
):
    """FAQ 상세 조회 (조회수 증가)"""
    return support_service.get_faq_by_id(faq_id)


@router.post("/faqs", response_model=FAQResponse)
async def create_faq(
    faq_data: FAQCreate,
    support_service: SupportService = Depends(get_support_service),
    current_admin: Admin = Depends(get_current_admin_user)
):
    """FAQ 생성 (관리자 전용)"""
    return support_service.create_faq(faq_data)


@router.put("/faqs/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: int,
    faq_data: FAQUpdate,
    support_service: SupportService = Depends(get_support_service),
    current_admin: Admin = Depends(get_current_admin_user)
):
    """FAQ 수정 (관리자 전용)"""
    return support_service.update_faq(faq_id, faq_data)


@router.delete("/faqs/{faq_id}")
async def delete_faq(
    faq_id: int,
    support_service: SupportService = Depends(get_support_service),
    current_admin: Admin = Depends(get_current_admin_user)
):
    """FAQ 삭제 (관리자 전용)"""
    support_service.delete_faq(faq_id)
    return {"message": "FAQ가 삭제되었습니다."}


# 1:1 문의 관련 엔드포인트
@router.post("/inquiries", response_model=InquiryResponse)
async def create_inquiry(
    inquiry_data: InquiryCreate,
    support_service: SupportService = Depends(get_support_service)
):
    """
    1:1 문의 접수
    
    고객이 문의를 접수할 수 있습니다. 인증이 필요하지 않습니다.
    """
    return support_service.create_inquiry(inquiry_data)


@router.get("/inquiries", response_model=InquiryListResponse)
async def get_inquiries(
    status: Optional[str] = Query(None, description="처리 상태 필터"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    search: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    support_service: SupportService = Depends(get_support_service),
    current_admin: Admin = Depends(get_current_admin_user)
):
    """문의 목록 조회 (관리자 전용)"""
    return support_service.get_inquiries(
        status=status,
        category=category,
        search=search,
        page=page,
        size=size
    )


@router.get("/inquiries/{inquiry_id}", response_model=InquiryResponse)
async def get_inquiry(
    inquiry_id: int,
    support_service: SupportService = Depends(get_support_service),
    current_admin: Admin = Depends(get_current_admin_user)
):
    """문의 상세 조회 (관리자 전용)"""
    return support_service.get_inquiry_by_id(inquiry_id)


@router.put("/inquiries/{inquiry_id}", response_model=InquiryResponse)
async def update_inquiry(
    inquiry_id: int,
    inquiry_data: InquiryUpdate,
    support_service: SupportService = Depends(get_support_service),
    current_admin: Admin = Depends(get_current_admin_user)
):
    """문의 답변 (관리자 전용)"""
    return support_service.update_inquiry(inquiry_id, inquiry_data)


@router.get("/categories", response_model=Dict[str, Any])
async def get_inquiry_categories(
    support_service: SupportService = Depends(get_support_service)
):
    """문의 카테고리 목록"""
    return {"categories": support_service.get_inquiry_categories()}