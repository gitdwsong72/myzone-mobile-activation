"""
시드 데이터 생성 스크립트
요구사항 2.1, 4.1에 따른 요금제, 단말기, 관리자 계정 초기 데이터
"""

import json

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Admin, Device, Number, Plan

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_seed_plans(db: Session):
    """요금제 시드 데이터 생성"""
    plans_data = [
        # 5G 요금제
        {
            "name": "5G 프리미엄",
            "description": "5G 무제한 데이터와 프리미엄 서비스를 제공하는 최고급 요금제",
            "category": "5G",
            "monthly_fee": 89000,
            "setup_fee": 0,
            "data_limit": None,  # 무제한
            "call_minutes": None,  # 무제한
            "sms_count": None,  # 무제한
            "additional_services": json.dumps(
                [
                    "5G 네트워크",
                    "무제한 데이터",
                    "무제한 통화",
                    "무제한 문자",
                    "Netflix 베이직",
                    "YouTube Premium",
                    "해외로밍 10GB",
                ]
            ),
            "discount_rate": 0,
            "promotion_text": "첫 3개월 50% 할인",
            "is_active": True,
            "display_order": 1,
        },
        {
            "name": "5G 스탠다드",
            "description": "합리적인 가격의 5G 요금제",
            "category": "5G",
            "monthly_fee": 69000,
            "setup_fee": 0,
            "data_limit": 100000,  # 100GB
            "call_minutes": None,  # 무제한
            "sms_count": None,  # 무제한
            "additional_services": json.dumps(["5G 네트워크", "100GB 데이터", "무제한 통화", "무제한 문자"]),
            "discount_rate": 10,
            "promotion_text": "신규 가입 10% 할인",
            "is_active": True,
            "display_order": 2,
        },
        # LTE 요금제
        {
            "name": "LTE 프리미엄",
            "description": "LTE 무제한 데이터 요금제",
            "category": "LTE",
            "monthly_fee": 55000,
            "setup_fee": 0,
            "data_limit": None,  # 무제한
            "call_minutes": None,  # 무제한
            "sms_count": None,  # 무제한
            "additional_services": json.dumps(["LTE 네트워크", "무제한 데이터", "무제한 통화", "무제한 문자"]),
            "discount_rate": 0,
            "promotion_text": None,
            "is_active": True,
            "display_order": 3,
        },
        {
            "name": "LTE 스탠다드",
            "description": "적당한 데이터와 합리적인 가격",
            "category": "LTE",
            "monthly_fee": 39000,
            "setup_fee": 0,
            "data_limit": 50000,  # 50GB
            "call_minutes": None,  # 무제한
            "sms_count": None,  # 무제한
            "additional_services": json.dumps(["LTE 네트워크", "50GB 데이터", "무제한 통화", "무제한 문자"]),
            "discount_rate": 0,
            "promotion_text": None,
            "is_active": True,
            "display_order": 4,
        },
        # 데이터 중심 요금제
        {
            "name": "데이터 무제한",
            "description": "데이터 사용량이 많은 고객을 위한 요금제",
            "category": "데이터중심",
            "monthly_fee": 49000,
            "setup_fee": 0,
            "data_limit": None,  # 무제한
            "call_minutes": 300,  # 300분
            "sms_count": 100,  # 100건
            "additional_services": json.dumps(["무제한 데이터", "300분 통화", "100건 문자"]),
            "discount_rate": 0,
            "promotion_text": "데이터 무제한 특가",
            "is_active": True,
            "display_order": 5,
        },
        # 통화 중심 요금제
        {
            "name": "통화 무제한",
            "description": "통화를 많이 하는 고객을 위한 요금제",
            "category": "통화중심",
            "monthly_fee": 35000,
            "setup_fee": 0,
            "data_limit": 10000,  # 10GB
            "call_minutes": None,  # 무제한
            "sms_count": None,  # 무제한
            "additional_services": json.dumps(["10GB 데이터", "무제한 통화", "무제한 문자"]),
            "discount_rate": 0,
            "promotion_text": None,
            "is_active": True,
            "display_order": 6,
        },
    ]

    for plan_data in plans_data:
        # 이미 존재하는지 확인
        existing_plan = db.query(Plan).filter(Plan.name == plan_data["name"]).first()
        if not existing_plan:
            plan = Plan(**plan_data)
            db.add(plan)

    db.commit()
    print("✅ 요금제 시드 데이터 생성 완료")


def create_seed_devices(db: Session):
    """단말기 시드 데이터 생성"""
    devices_data = [
        # 삼성 갤럭시
        {
            "brand": "삼성",
            "model": "갤럭시 S24 Ultra",
            "color": "티타늄 그레이",
            "price": 1398000,
            "discount_price": 1298000,
            "stock_quantity": 50,
            "specifications": json.dumps(
                {
                    "display": "6.8인치 Dynamic AMOLED 2X",
                    "processor": "Snapdragon 8 Gen 3",
                    "memory": "12GB RAM",
                    "storage": "256GB",
                    "camera": "200MP 메인 + 50MP 망원 + 12MP 초광각 + 10MP 망원",
                    "battery": "5000mAh",
                    "os": "Android 14",
                }
            ),
            "description": "최고 성능의 프리미엄 스마트폰",
            "image_url": "/images/devices/galaxy-s24-ultra-gray.jpg",
            "image_urls": json.dumps(
                ["/images/devices/galaxy-s24-ultra-gray-1.jpg", "/images/devices/galaxy-s24-ultra-gray-2.jpg"]
            ),
            "is_active": True,
            "is_featured": True,
            "display_order": 1,
            "release_date": "2024-01",
        },
        {
            "brand": "삼성",
            "model": "갤럭시 S24",
            "color": "온익스 블랙",
            "price": 998000,
            "discount_price": 898000,
            "stock_quantity": 75,
            "specifications": json.dumps(
                {
                    "display": "6.2인치 Dynamic AMOLED 2X",
                    "processor": "Exynos 2400",
                    "memory": "8GB RAM",
                    "storage": "256GB",
                    "camera": "50MP 메인 + 12MP 초광각 + 10MP 망원",
                    "battery": "4000mAh",
                    "os": "Android 14",
                }
            ),
            "description": "컴팩트한 프리미엄 스마트폰",
            "image_url": "/images/devices/galaxy-s24-black.jpg",
            "is_active": True,
            "is_featured": True,
            "display_order": 2,
            "release_date": "2024-01",
        },
        # 애플 아이폰
        {
            "brand": "애플",
            "model": "아이폰 15 Pro Max",
            "color": "내추럴 티타늄",
            "price": 1550000,
            "discount_price": None,
            "stock_quantity": 30,
            "specifications": json.dumps(
                {
                    "display": "6.7인치 Super Retina XDR",
                    "processor": "A17 Pro",
                    "memory": "8GB RAM",
                    "storage": "256GB",
                    "camera": "48MP 메인 + 12MP 초광각 + 12MP 망원",
                    "battery": "4441mAh",
                    "os": "iOS 17",
                }
            ),
            "description": "최신 아이폰 프로 맥스",
            "image_url": "/images/devices/iphone-15-pro-max-titanium.jpg",
            "is_active": True,
            "is_featured": True,
            "display_order": 3,
            "release_date": "2023-09",
        },
        {
            "brand": "애플",
            "model": "아이폰 15",
            "color": "핑크",
            "price": 1250000,
            "discount_price": 1150000,
            "stock_quantity": 45,
            "specifications": json.dumps(
                {
                    "display": "6.1인치 Super Retina XDR",
                    "processor": "A16 Bionic",
                    "memory": "6GB RAM",
                    "storage": "128GB",
                    "camera": "48MP 메인 + 12MP 초광각",
                    "battery": "3349mAh",
                    "os": "iOS 17",
                }
            ),
            "description": "스탠다드 아이폰 15",
            "image_url": "/images/devices/iphone-15-pink.jpg",
            "is_active": True,
            "is_featured": False,
            "display_order": 4,
            "release_date": "2023-09",
        },
        # LG
        {
            "brand": "LG",
            "model": "LG V60 ThinQ",
            "color": "오로라 그레이",
            "price": 598000,
            "discount_price": 498000,
            "stock_quantity": 20,
            "specifications": json.dumps(
                {
                    "display": "6.8인치 P-OLED",
                    "processor": "Snapdragon 865",
                    "memory": "8GB RAM",
                    "storage": "128GB",
                    "camera": "64MP 메인 + 13MP 초광각",
                    "battery": "5000mAh",
                    "os": "Android 10",
                }
            ),
            "description": "합리적인 가격의 프리미엄 스마트폰",
            "image_url": "/images/devices/lg-v60-gray.jpg",
            "is_active": True,
            "is_featured": False,
            "display_order": 5,
            "release_date": "2020-03",
        },
    ]

    for device_data in devices_data:
        # 이미 존재하는지 확인 (브랜드, 모델, 색상 조합으로)
        existing_device = (
            db.query(Device)
            .filter(
                Device.brand == device_data["brand"],
                Device.model == device_data["model"],
                Device.color == device_data["color"],
            )
            .first()
        )

        if not existing_device:
            device = Device(**device_data)
            db.add(device)

    db.commit()
    print("✅ 단말기 시드 데이터 생성 완료")


def create_seed_numbers(db: Session):
    """전화번호 시드 데이터 생성"""
    numbers_data = [
        # 일반 번호
        {"number": "010-1234-5678", "category": "일반", "additional_fee": 0, "is_premium": False},
        {"number": "010-2345-6789", "category": "일반", "additional_fee": 0, "is_premium": False},
        {"number": "010-3456-7890", "category": "일반", "additional_fee": 0, "is_premium": False},
        {"number": "010-4567-8901", "category": "일반", "additional_fee": 0, "is_premium": False},
        {"number": "010-5678-9012", "category": "일반", "additional_fee": 0, "is_premium": False},
        # 연속 번호
        {"number": "010-1111-2345", "category": "연속", "additional_fee": 50000, "is_premium": True, "pattern_type": "연속"},
        {"number": "010-2222-3456", "category": "연속", "additional_fee": 50000, "is_premium": True, "pattern_type": "연속"},
        {"number": "010-3333-4567", "category": "연속", "additional_fee": 50000, "is_premium": True, "pattern_type": "연속"},
        {"number": "010-1234-5678", "category": "연속", "additional_fee": 100000, "is_premium": True, "pattern_type": "연속"},
        # 특별 번호
        {"number": "010-7777-7777", "category": "특별", "additional_fee": 200000, "is_premium": True, "pattern_type": "반복"},
        {"number": "010-8888-8888", "category": "특별", "additional_fee": 200000, "is_premium": True, "pattern_type": "반복"},
        {"number": "010-9999-9999", "category": "특별", "additional_fee": 300000, "is_premium": True, "pattern_type": "반복"},
        {"number": "010-1004-1004", "category": "특별", "additional_fee": 150000, "is_premium": True, "pattern_type": "대칭"},
        {"number": "010-2002-2002", "category": "특별", "additional_fee": 150000, "is_premium": True, "pattern_type": "대칭"},
    ]

    for number_data in numbers_data:
        # 이미 존재하는지 확인
        existing_number = db.query(Number).filter(Number.number == number_data["number"]).first()
        if not existing_number:
            number = Number(**number_data)
            db.add(number)

    db.commit()
    print("✅ 전화번호 시드 데이터 생성 완료")


def create_seed_admins(db: Session):
    """관리자 계정 시드 데이터 생성"""
    admins_data = [
        {
            "username": "admin",
            "email": "admin@myzone.com",
            "password_hash": pwd_context.hash("admin123!"),
            "role": "super_admin",
            "is_active": True,
            "is_superuser": True,
            "full_name": "시스템 관리자",
            "department": "IT팀",
            "phone": "02-1234-5678",
            "login_count": "0",
        },
        {
            "username": "operator1",
            "email": "operator1@myzone.com",
            "password_hash": pwd_context.hash("operator123!"),
            "role": "operator",
            "is_active": True,
            "is_superuser": False,
            "full_name": "운영자1",
            "department": "고객서비스팀",
            "phone": "02-1234-5679",
            "login_count": "0",
        },
        {
            "username": "operator2",
            "email": "operator2@myzone.com",
            "password_hash": pwd_context.hash("operator123!"),
            "role": "operator",
            "is_active": True,
            "is_superuser": False,
            "full_name": "운영자2",
            "department": "고객서비스팀",
            "phone": "02-1234-5680",
            "login_count": "0",
        },
    ]

    for admin_data in admins_data:
        # 이미 존재하는지 확인
        existing_admin = db.query(Admin).filter(Admin.username == admin_data["username"]).first()
        if not existing_admin:
            admin = Admin(**admin_data)
            db.add(admin)

    db.commit()
    print("✅ 관리자 계정 시드 데이터 생성 완료")


def run_seed_data():
    """모든 시드 데이터 실행"""
    db = SessionLocal()
    try:
        print("🌱 시드 데이터 생성 시작...")

        create_seed_plans(db)
        create_seed_devices(db)
        create_seed_numbers(db)
        create_seed_admins(db)

        print("🎉 모든 시드 데이터 생성 완료!")

    except Exception as e:
        print(f"❌ 시드 데이터 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_seed_data()
