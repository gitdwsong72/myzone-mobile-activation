import math
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ..models.faq import FAQ, Inquiry
from ..schemas.support import (
    FAQCreate,
    FAQListResponse,
    FAQResponse,
    FAQUpdate,
    InquiryCreate,
    InquiryListResponse,
    InquiryResponse,
    InquiryUpdate,
)


class SupportService:
    def __init__(self, db: Session):
        self.db = db

    def get_faqs(
        self, category: Optional[str] = None, search: Optional[str] = None, is_active: bool = True
    ) -> FAQListResponse:
        """FAQ 목록 조회"""
        query = self.db.query(FAQ)

        if is_active:
            query = query.filter(FAQ.is_active == True)

        if category:
            query = query.filter(FAQ.category == category)

        if search:
            query = query.filter(or_(FAQ.question.ilike(f"%{search}%"), FAQ.answer.ilike(f"%{search}%")))

        faqs = query.order_by(FAQ.view_count.desc(), FAQ.created_at.desc()).all()
        total = len(faqs)

        # 카테고리 목록 조회
        categories = self.db.query(FAQ.category).filter(FAQ.is_active == True).distinct().all()
        categories = [cat[0] for cat in categories]

        return FAQListResponse(faqs=[FAQResponse.from_orm(faq) for faq in faqs], total=total, categories=categories)

    def get_faq_by_id(self, faq_id: int) -> FAQResponse:
        """FAQ 상세 조회"""
        faq = self.db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not faq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ를 찾을 수 없습니다.")

        # 조회수 증가
        faq.view_count += 1
        self.db.commit()
        self.db.refresh(faq)

        return FAQResponse.from_orm(faq)

    def create_faq(self, faq_data: FAQCreate) -> FAQResponse:
        """FAQ 생성 (관리자 전용)"""
        faq = FAQ(**faq_data.dict())
        self.db.add(faq)
        self.db.commit()
        self.db.refresh(faq)
        return FAQResponse.from_orm(faq)

    def update_faq(self, faq_id: int, faq_data: FAQUpdate) -> FAQResponse:
        """FAQ 수정 (관리자 전용)"""
        faq = self.db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not faq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ를 찾을 수 없습니다.")

        update_data = faq_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(faq, field, value)

        self.db.commit()
        self.db.refresh(faq)
        return FAQResponse.from_orm(faq)

    def delete_faq(self, faq_id: int) -> bool:
        """FAQ 삭제 (관리자 전용)"""
        faq = self.db.query(FAQ).filter(FAQ.id == faq_id).first()
        if not faq:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ를 찾을 수 없습니다.")

        self.db.delete(faq)
        self.db.commit()
        return True

    def create_inquiry(self, inquiry_data: InquiryCreate) -> InquiryResponse:
        """1:1 문의 생성"""
        inquiry = Inquiry(**inquiry_data.dict())
        self.db.add(inquiry)
        self.db.commit()
        self.db.refresh(inquiry)
        return InquiryResponse.from_orm(inquiry)

    def get_inquiries(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> InquiryListResponse:
        """문의 목록 조회 (관리자 전용)"""
        query = self.db.query(Inquiry)

        if status:
            query = query.filter(Inquiry.status == status)

        if category:
            query = query.filter(Inquiry.category == category)

        if search:
            query = query.filter(
                or_(
                    Inquiry.name.ilike(f"%{search}%"),
                    Inquiry.email.ilike(f"%{search}%"),
                    Inquiry.subject.ilike(f"%{search}%"),
                    Inquiry.order_number.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        total_pages = math.ceil(total / size)

        inquiries = query.order_by(Inquiry.created_at.desc()).offset((page - 1) * size).limit(size).all()

        return InquiryListResponse(
            inquiries=[InquiryResponse.from_orm(inquiry) for inquiry in inquiries],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )

    def get_inquiry_by_id(self, inquiry_id: int) -> InquiryResponse:
        """문의 상세 조회"""
        inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")

        return InquiryResponse.from_orm(inquiry)

    def update_inquiry(self, inquiry_id: int, inquiry_data: InquiryUpdate) -> InquiryResponse:
        """문의 답변 (관리자 전용)"""
        inquiry = self.db.query(Inquiry).filter(Inquiry.id == inquiry_id).first()
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문의를 찾을 수 없습니다.")

        update_data = inquiry_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(inquiry, field, value)

        # 답변이 있으면 답변 일시 설정
        if inquiry_data.admin_reply:
            inquiry.replied_at = func.now()
            inquiry.status = "replied"

        self.db.commit()
        self.db.refresh(inquiry)
        return InquiryResponse.from_orm(inquiry)

    def get_inquiry_categories(self) -> List[str]:
        """문의 카테고리 목록"""
        return ["요금제", "개통절차", "결제", "배송", "단말기", "번호", "기타"]
