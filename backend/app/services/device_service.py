import os
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ..models.device import Device
from ..schemas.device import BrandInfo, DeviceCreate, DeviceFilter, DeviceUpdate
from .cache_service import cache_service


class DeviceService:
    """단말기 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.cache = cache_service

    def get_devices(self, filters: DeviceFilter, page: int = 1, size: int = 20) -> tuple[List[Device], int]:
        """단말기 목록 조회 (필터링 및 페이징 지원)"""
        query = self.db.query(Device)

        # 필터 적용
        conditions = []

        if filters.brand:
            conditions.append(Device.brand == filters.brand)

        if filters.min_price is not None:
            conditions.append(Device.price >= filters.min_price)

        if filters.max_price is not None:
            conditions.append(Device.price <= filters.max_price)

        if filters.in_stock_only:
            conditions.append(Device.stock_quantity > 0)

        if filters.is_active is not None:
            conditions.append(Device.is_active == filters.is_active)

        if filters.is_featured is not None:
            conditions.append(Device.is_featured == filters.is_featured)

        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(
                or_(Device.brand.ilike(search_term), Device.model.ilike(search_term), Device.description.ilike(search_term))
            )

        if conditions:
            query = query.filter(and_(*conditions))

        # 전체 개수 조회
        total = query.count()

        # 정렬 및 페이징 (추천 상품 우선, 브랜드별, 표시 순서별)
        devices = (
            query.order_by(Device.is_featured.desc(), Device.brand.asc(), Device.display_order.asc(), Device.id.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return devices, total

    def get_device_by_id(self, device_id: int) -> Device:
        """ID로 단말기 조회 (캐시 적용)"""
        # 캐시에서 조회
        cached_device = self.cache.get_cached_device(device_id)
        if cached_device:
            return Device(**cached_device)

        # 캐시 미스 시 DB에서 조회
        device = self.db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="단말기를 찾을 수 없습니다.")

        # 결과 캐싱
        device_dict = {
            "id": device.id,
            "brand": device.brand,
            "model": device.model,
            "color": device.color,
            "price": float(device.price),
            "discount_price": float(device.discount_price) if device.discount_price else None,
            "stock_quantity": device.stock_quantity,
            "specifications": device.specifications,
            "description": device.description,
            "image_url": device.image_url,
            "image_urls": device.image_urls,
            "is_active": device.is_active,
            "is_featured": device.is_featured,
            "display_order": device.display_order,
            "release_date": device.release_date,
            "created_at": device.created_at.isoformat() if device.created_at else None,
            "updated_at": device.updated_at.isoformat() if device.updated_at else None,
        }
        self.cache.cache_device(device_id, device_dict)

        return device

    def get_devices_by_brand(self, brand: str) -> List[Device]:
        """브랜드별 단말기 조회 (캐시 적용)"""
        # 캐시에서 조회
        cached_devices = self.cache.get_cached_devices_list(brand)
        if cached_devices:
            return [Device(**device_data) for device_data in cached_devices]

        # 캐시 미스 시 DB에서 조회
        devices = (
            self.db.query(Device)
            .filter(and_(Device.brand == brand, Device.is_active == True))
            .order_by(Device.display_order.asc(), Device.id.asc())
            .all()
        )

        # 결과 캐싱
        devices_data = []
        for device in devices:
            device_dict = {
                "id": device.id,
                "brand": device.brand,
                "model": device.model,
                "color": device.color,
                "price": float(device.price),
                "discount_price": float(device.discount_price) if device.discount_price else None,
                "stock_quantity": device.stock_quantity,
                "specifications": device.specifications,
                "description": device.description,
                "image_url": device.image_url,
                "image_urls": device.image_urls,
                "is_active": device.is_active,
                "is_featured": device.is_featured,
                "display_order": device.display_order,
                "release_date": device.release_date,
                "created_at": device.created_at.isoformat() if device.created_at else None,
                "updated_at": device.updated_at.isoformat() if device.updated_at else None,
            }
            devices_data.append(device_dict)

        self.cache.cache_devices_list(brand, devices_data)
        return devices

    def get_available_brands(self) -> List[BrandInfo]:
        """사용 가능한 브랜드 목록 조회"""
        brands_data = (
            self.db.query(
                Device.brand,
                func.count(Device.id).label("device_count"),
                func.array_agg(Device.model.distinct()).label("models"),
            )
            .filter(Device.is_active == True)
            .group_by(Device.brand)
            .order_by(Device.brand.asc())
            .all()
        )

        return [
            BrandInfo(brand=brand, device_count=count, models=list(set(models)) if models else [])
            for brand, count, models in brands_data
        ]

    def get_featured_devices(self, limit: int = 6) -> List[Device]:
        """추천 단말기 조회"""
        return (
            self.db.query(Device)
            .filter(and_(Device.is_featured == True, Device.is_active == True))
            .order_by(Device.display_order.asc(), Device.id.asc())
            .limit(limit)
            .all()
        )

    def get_devices_in_stock(self) -> List[Device]:
        """재고 있는 단말기 조회"""
        return (
            self.db.query(Device)
            .filter(and_(Device.stock_quantity > 0, Device.is_active == True))
            .order_by(Device.brand.asc(), Device.display_order.asc())
            .all()
        )

    def check_stock(self, device_id: int, quantity: int = 1) -> bool:
        """재고 확인"""
        device = self.get_device_by_id(device_id)
        return device.stock_quantity >= quantity

    def update_stock(self, device_id: int, quantity: int) -> Device:
        """재고 수량 업데이트"""
        device = self.get_device_by_id(device_id)
        device.stock_quantity = quantity
        self.db.commit()
        self.db.refresh(device)

        # 캐시 무효화 (재고 변경 시)
        self.cache.invalidate_device_cache(device_id)

        return device

    def decrease_stock(self, device_id: int, quantity: int = 1) -> Device:
        """재고 차감"""
        device = self.get_device_by_id(device_id)
        if device.stock_quantity < quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="재고가 부족합니다.")
        device.stock_quantity -= quantity
        self.db.commit()
        self.db.refresh(device)
        return device

    def create_device(self, device_data: DeviceCreate) -> Device:
        """단말기 생성 (관리자용)"""
        device = Device(**device_data.model_dump())
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)

        # 캐시 무효화
        self.cache.invalidate_device_cache()

        return device

    def update_device(self, device_id: int, device_data: DeviceUpdate) -> Device:
        """단말기 수정 (관리자용)"""
        device = self.get_device_by_id(device_id)

        update_data = device_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(device, field, value)

        self.db.commit()
        self.db.refresh(device)

        # 캐시 무효화
        self.cache.invalidate_device_cache(device_id)

        return device

    def delete_device(self, device_id: int) -> bool:
        """단말기 삭제 (관리자용) - 소프트 삭제"""
        device = self.get_device_by_id(device_id)
        device.is_active = False
        self.db.commit()
        return True

    def upload_device_image(self, device_id: int, file: UploadFile, is_main: bool = False) -> str:
        """단말기 이미지 업로드"""
        device = self.get_device_by_id(device_id)

        # 파일 확장자 검증
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지원하지 않는 이미지 형식입니다.")

        # 파일명 생성
        filename = f"{uuid.uuid4()}{file_extension}"
        upload_dir = Path("uploads/devices")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename

        # 파일 저장
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)

        # URL 생성
        image_url = f"/uploads/devices/{filename}"

        # 데이터베이스 업데이트
        if is_main:
            device.image_url = image_url
        else:
            if device.image_urls is None:
                device.image_urls = []
            device.image_urls.append(image_url)

        self.db.commit()
        self.db.refresh(device)

        return image_url

    def remove_device_image(self, device_id: int, image_url: str) -> bool:
        """단말기 이미지 삭제"""
        device = self.get_device_by_id(device_id)

        if device.image_url == image_url:
            device.image_url = None
        elif device.image_urls and image_url in device.image_urls:
            device.image_urls.remove(image_url)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="이미지를 찾을 수 없습니다.")

        # 실제 파일 삭제
        try:
            file_path = Path(f".{image_url}")
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass  # 파일 삭제 실패는 무시

        self.db.commit()
        return True

    async def update_device_images(self, device_id: int, image_urls: dict) -> Device:
        """단말기 이미지 URL 업데이트"""
        device = self.get_device_by_id(device_id)

        # 메인 이미지 URL 설정 (large 크기 사용)
        if "large" in image_urls:
            device.image_url = image_urls["large"]

        # 모든 크기의 이미지 URL을 JSON으로 저장
        device.image_urls = image_urls

        self.db.commit()
        self.db.refresh(device)
        return device
