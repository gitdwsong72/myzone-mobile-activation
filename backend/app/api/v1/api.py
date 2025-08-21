from fastapi import APIRouter

from . import admin, auth, devices, files, notifications, numbers, orders, payments, plans, sms, support, users

api_router = APIRouter()

# 인증 관련 라우터
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 관리자 관련 라우터
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# 사용자 관련 라우터
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 요금제 관련 라우터
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])

# 단말기 관련 라우터
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])

# 전화번호 관련 라우터
api_router.include_router(numbers.router, prefix="/numbers", tags=["numbers"])

# 주문 관련 라우터
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])

# 결제 관련 라우터
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])

# SMS 관련 라우터
api_router.include_router(sms.router, prefix="/sms", tags=["sms"])

# 알림 관련 라우터
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# 고객지원 관련 라우터
api_router.include_router(support.router, prefix="/support", tags=["support"])

# 파일 관련 라우터
api_router.include_router(files.router, prefix="/files", tags=["files"])


@api_router.get("/")
async def api_root():
    return {"message": "MyZone API v1"}
