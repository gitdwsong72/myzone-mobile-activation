from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from decimal import Decimal
import math

from ...core.database import get_db
from ...core.deps import get_current_admin
from ...services.device_service import DeviceService
from ...schemas.device import (
    DeviceResponse, 
    DeviceListResponse, 
    DeviceCreate, 
    DeviceUpdate,
    DeviceFilter,
    DeviceStockUpdate,
    BrandInfo
)
from ...models.admin import Admin

router = APIRouter()


def get_device_service(db: Session = Depends(get_db)) -> DeviceService:
    """단말기 서비스 의존성"""
    return DeviceService(db)


@router.get("/", response_model=DeviceListResponse)
async def get_devices(
    brand: Optional[str] = Query(None, description="브랜드 필터"),
    min_price: Optional[Decimal] = Query(None, description="최소 가격"),
    max_price: Optional[Decimal] = Query(None, description="최대 가격"),
    in_stock_only: Optional[bool] = Query(None, description="재고 있는 상품만"),
    search: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    단말기 목록 조회
    
    - **brand**: 브랜드별 필터링
    - **min_price**: 최소 가격 필터
    - **max_price**: 최대 가격 필터
    - **in_stock_only**: 재고 있는 상품만 조회
    - **search**: 브랜드, 모델명 검색
    - **page**: 페이지 번호 (기본값: 1)
    - **size**: 페이지 크기 (기본값: 20, 최대: 100)
    """
    filters = DeviceFilter(
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        search=search,
        is_active=True
    )
    
    devices, total = device_service.get_devices(filters, page, size)
    total_pages = math.ceil(total / size)
    
    return DeviceListResponse(
        devices=devices,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get("/brands", response_model=List[BrandInfo])
async def get_device_brands(
    device_service: DeviceService = Depends(get_device_service)
):
    """
    사용 가능한 단말기 브랜드 목록 조회
    """
    return device_service.get_available_brands()


@router.get("/featured", response_model=List[DeviceResponse])
async def get_featured_devices(
    limit: int = Query(6, ge=1, le=20, description="추천 단말기 개수"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    추천 단말기 조회
    """
    return device_service.get_featured_devices(limit)


@router.get("/in-stock", response_model=List[DeviceResponse])
async def get_devices_in_stock(
    device_service: DeviceService = Depends(get_device_service)
):
    """
    재고 있는 단말기 목록 조회
    """
    return device_service.get_devices_in_stock()


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service)
):
    """
    단말기 상세 정보 조회
    """
    device = device_service.get_device_by_id(device_id)
    if not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="단말기를 찾을 수 없습니다."
        )
    return device


@router.get("/{device_id}/stock")
async def check_device_stock(
    device_id: int,
    quantity: int = Query(1, ge=1, description="확인할 수량"),
    device_service: DeviceService = Depends(get_device_service)
):
    """
    단말기 재고 확인
    """
    is_available = device_service.check_stock(device_id, quantity)
    device = device_service.get_device_by_id(device_id)
    
    return {
        "device_id": device_id,
        "current_stock": device.stock_quantity,
        "requested_quantity": quantity,
        "is_available": is_available
    }


# 관리자 전용 엔드포인트
@router.post("/", response_model=DeviceResponse)
async def create_device(
    device_data: DeviceCreate,
    device_service: DeviceService = Depends(get_device_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    단말기 생성 (관리자 전용)
    """
    return device_service.create_device(device_data)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    device_service: DeviceService = Depends(get_device_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    단말기 수정 (관리자 전용)
    """
    return device_service.update_device(device_id, device_data)


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    device_service: DeviceService = Depends(get_device_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    단말기 삭제 (관리자 전용) - 소프트 삭제
    """
    device_service.delete_device(device_id)
    return {"message": "단말기가 삭제되었습니다."}


@router.put("/{device_id}/stock", response_model=DeviceResponse)
async def update_device_stock(
    device_id: int,
    stock_data: DeviceStockUpdate,
    device_service: DeviceService = Depends(get_device_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    단말기 재고 수량 업데이트 (관리자 전용)
    """
    return device_service.update_stock(device_id, stock_data.stock_quantity)


@router.post("/{device_id}/images")
async def upload_device_image(
    device_id: int,
    file: UploadFile = File(...),
    is_main: bool = Query(False, description="대표 이미지 여부"),
    device_service: DeviceService = Depends(get_device_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    단말기 이미지 업로드 (관리자 전용)
    """
    # 파일 크기 제한 (5MB)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일 크기는 5MB를 초과할 수 없습니다."
        )
    
    image_url = device_service.upload_device_image(device_id, file, is_main)
    return {"image_url": image_url, "message": "이미지가 업로드되었습니다."}


@router.delete("/{device_id}/images")
async def remove_device_image(
    device_id: int,
    image_url: str = Query(..., description="삭제할 이미지 URL"),
    device_service: DeviceService = Depends(get_device_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    단말기 이미지 삭제 (관리자 전용)
    """
    device_service.remove_device_image(device_id, image_url)
    return {"message": "이미지가 삭제되었습니다."}


@router.get("/admin/all", response_model=DeviceListResponse)
async def get_all_devices_for_admin(
    brand: Optional[str] = Query(None, description="브랜드 필터"),
    min_price: Optional[Decimal] = Query(None, description="최소 가격"),
    max_price: Optional[Decimal] = Query(None, description="최대 가격"),
    in_stock_only: Optional[bool] = Query(None, description="재고 있는 상품만"),
    is_active: Optional[bool] = Query(None, description="활성화 상태"),
    is_featured: Optional[bool] = Query(None, description="추천 상품 필터"),
    search: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    device_service: DeviceService = Depends(get_device_service),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    모든 단말기 조회 (관리자 전용) - 비활성화된 단말기 포함
    """
    filters = DeviceFilter(
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        is_active=is_active,
        is_featured=is_featured,
        search=search
    )
    
    devices, total = device_service.get_devices(filters, page, size)
    total_pages = math.ceil(total / size)
    
    return DeviceListResponse(
        devices=devices,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )