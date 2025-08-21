import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, desc, extract, func, or_
from sqlalchemy.orm import Session

from ..models.device import Device
from ..models.order import Order
from ..models.order_status_history import OrderStatusHistory
from ..models.payment import Payment
from ..models.plan import Plan
from ..models.user import User


class StatisticsService:
    """통계 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_overview_stats(self) -> Dict[str, Any]:
        """전체 개요 통계"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = this_month_start - timedelta(days=1)

        # 기본 통계
        total_users = self.db.query(User).count()
        total_orders = self.db.query(Order).count()
        total_revenue = self.db.query(func.sum(Order.total_amount)).filter(Order.status == "completed").scalar() or Decimal(
            "0"
        )

        # 오늘 통계
        today_orders = self.db.query(Order).filter(func.date(Order.created_at) == today).count()

        today_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            and_(func.date(Order.created_at) == today, Order.status == "completed")
        ).scalar() or Decimal("0")

        # 어제 통계 (비교용)
        yesterday_orders = self.db.query(Order).filter(func.date(Order.created_at) == yesterday).count()

        yesterday_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            and_(func.date(Order.created_at) == yesterday, Order.status == "completed")
        ).scalar() or Decimal("0")

        # 이번 달 통계
        this_month_orders = self.db.query(Order).filter(Order.created_at >= this_month_start).count()

        this_month_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            and_(Order.created_at >= this_month_start, Order.status == "completed")
        ).scalar() or Decimal("0")

        # 지난 달 통계 (비교용)
        last_month_orders = (
            self.db.query(Order).filter(and_(Order.created_at >= last_month_start, Order.created_at <= last_month_end)).count()
        )

        last_month_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            and_(Order.created_at >= last_month_start, Order.created_at <= last_month_end, Order.status == "completed")
        ).scalar() or Decimal("0")

        # 성장률 계산
        def calculate_growth_rate(current: float, previous: float) -> float:
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round(((current - previous) / previous) * 100, 2)

        return {
            "overview": {"total_users": total_users, "total_orders": total_orders, "total_revenue": float(total_revenue)},
            "today": {
                "orders": today_orders,
                "revenue": float(today_revenue),
                "orders_growth": calculate_growth_rate(today_orders, yesterday_orders),
                "revenue_growth": calculate_growth_rate(float(today_revenue), float(yesterday_revenue)),
            },
            "this_month": {
                "orders": this_month_orders,
                "revenue": float(this_month_revenue),
                "orders_growth": calculate_growth_rate(this_month_orders, last_month_orders),
                "revenue_growth": calculate_growth_rate(float(this_month_revenue), float(last_month_revenue)),
            },
        }

    def get_order_status_stats(self) -> Dict[str, Any]:
        """주문 상태별 통계"""
        # 상태별 주문 수
        status_counts = self.db.query(Order.status, func.count(Order.id).label("count")).group_by(Order.status).all()

        total_orders = sum(count for _, count in status_counts)

        status_stats = []
        for status, count in status_counts:
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            status_stats.append({"status": status, "count": count, "percentage": round(percentage, 2)})

        # 처리 시간 통계 (완료된 주문만)
        processing_times = (
            self.db.query(
                func.avg(func.extract("epoch", OrderStatusHistory.created_at) - func.extract("epoch", Order.created_at)).label(
                    "avg_processing_time"
                )
            )
            .join(OrderStatusHistory, Order.id == OrderStatusHistory.order_id)
            .filter(and_(Order.status == "completed", OrderStatusHistory.status == "completed"))
            .scalar()
        )

        avg_processing_hours = round(processing_times / 3600, 2) if processing_times else 0

        return {
            "status_distribution": status_stats,
            "total_orders": total_orders,
            "avg_processing_hours": avg_processing_hours,
        }

    def get_daily_stats(self, days: int = 30) -> Dict[str, Any]:
        """일별 통계 (최근 N일)"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)

        # 일별 주문 수와 매출
        daily_stats = (
            self.db.query(
                func.date(Order.created_at).label("date"),
                func.count(Order.id).label("orders"),
                func.sum(case((Order.status == "completed", Order.total_amount), else_=0)).label("revenue"),
            )
            .filter(and_(func.date(Order.created_at) >= start_date, func.date(Order.created_at) <= end_date))
            .group_by(func.date(Order.created_at))
            .order_by(func.date(Order.created_at))
            .all()
        )

        # 모든 날짜에 대해 데이터 생성 (빈 날짜는 0으로)
        daily_data = []
        current_date = start_date
        stats_dict = {stat.date: stat for stat in daily_stats}

        while current_date <= end_date:
            stat = stats_dict.get(current_date)
            daily_data.append(
                {
                    "date": current_date.isoformat(),
                    "orders": stat.orders if stat else 0,
                    "revenue": float(stat.revenue) if stat and stat.revenue else 0.0,
                }
            )
            current_date += timedelta(days=1)

        return {"period": f"{start_date.isoformat()} ~ {end_date.isoformat()}", "daily_stats": daily_data}

    def get_monthly_stats(self, months: int = 12) -> Dict[str, Any]:
        """월별 통계 (최근 N개월)"""
        today = date.today()

        monthly_data = []
        for i in range(months):
            # 해당 월의 첫째 날과 마지막 날 계산
            if i == 0:
                month_start = today.replace(day=1)
                month_end = today
            else:
                month_start = today.replace(day=1) - timedelta(days=1)
                for _ in range(i - 1):
                    month_start = month_start.replace(day=1) - timedelta(days=1)
                month_start = month_start.replace(day=1)

                # 해당 월의 마지막 날
                next_month = month_start.replace(day=28) + timedelta(days=4)
                month_end = next_month - timedelta(days=next_month.day)

            # 해당 월의 통계
            month_orders = (
                self.db.query(Order)
                .filter(and_(func.date(Order.created_at) >= month_start, func.date(Order.created_at) <= month_end))
                .count()
            )

            month_revenue = self.db.query(func.sum(Order.total_amount)).filter(
                and_(
                    func.date(Order.created_at) >= month_start,
                    func.date(Order.created_at) <= month_end,
                    Order.status == "completed",
                )
            ).scalar() or Decimal("0")

            monthly_data.insert(
                0,
                {
                    "year": month_start.year,
                    "month": month_start.month,
                    "month_name": calendar.month_name[month_start.month],
                    "orders": month_orders,
                    "revenue": float(month_revenue),
                },
            )

        return {"monthly_stats": monthly_data}

    def get_plan_stats(self) -> Dict[str, Any]:
        """요금제별 통계"""
        # 요금제별 주문 수와 매출
        plan_stats = (
            self.db.query(
                Plan.id,
                Plan.name,
                Plan.monthly_fee,
                func.count(Order.id).label("order_count"),
                func.sum(Order.total_amount).label("total_revenue"),
                func.avg(Order.total_amount).label("avg_order_value"),
            )
            .join(Order, Plan.id == Order.plan_id)
            .group_by(Plan.id, Plan.name, Plan.monthly_fee)
            .order_by(desc(func.count(Order.id)))
            .all()
        )

        total_orders = sum(stat.order_count for stat in plan_stats)

        plan_data = []
        for stat in plan_stats:
            market_share = (stat.order_count / total_orders * 100) if total_orders > 0 else 0
            plan_data.append(
                {
                    "plan_id": stat.id,
                    "plan_name": stat.name,
                    "monthly_fee": float(stat.monthly_fee),
                    "order_count": stat.order_count,
                    "total_revenue": float(stat.total_revenue or 0),
                    "avg_order_value": float(stat.avg_order_value or 0),
                    "market_share": round(market_share, 2),
                }
            )

        return {"plan_stats": plan_data, "total_orders": total_orders}

    def get_device_stats(self) -> Dict[str, Any]:
        """단말기별 통계"""
        # 브랜드별 통계
        brand_stats = (
            self.db.query(
                Device.brand, func.count(Order.id).label("order_count"), func.sum(Order.device_fee).label("total_revenue")
            )
            .join(Order, Device.id == Order.device_id)
            .group_by(Device.brand)
            .order_by(desc(func.count(Order.id)))
            .all()
        )

        # 인기 단말기 (상위 10개)
        popular_devices = (
            self.db.query(
                Device.id, Device.brand, Device.model, Device.color, Device.price, func.count(Order.id).label("order_count")
            )
            .join(Order, Device.id == Order.device_id)
            .group_by(Device.id, Device.brand, Device.model, Device.color, Device.price)
            .order_by(desc(func.count(Order.id)))
            .limit(10)
            .all()
        )

        return {
            "brand_stats": [
                {"brand": stat.brand, "order_count": stat.order_count, "total_revenue": float(stat.total_revenue or 0)}
                for stat in brand_stats
            ],
            "popular_devices": [
                {
                    "device_id": device.id,
                    "brand": device.brand,
                    "model": device.model,
                    "color": device.color,
                    "price": float(device.price),
                    "order_count": device.order_count,
                }
                for device in popular_devices
            ],
        }

    def get_user_stats(self) -> Dict[str, Any]:
        """사용자 통계"""
        today = date.today()
        this_month_start = today.replace(day=1)

        # 전체 사용자 수
        total_users = self.db.query(User).count()

        # 이번 달 신규 사용자
        new_users_this_month = self.db.query(User).filter(User.created_at >= this_month_start).count()

        # 주문한 사용자 수
        users_with_orders = self.db.query(func.count(func.distinct(Order.user_id))).scalar()

        # 연령대별 통계 (생년월일 기준)
        age_stats = (
            self.db.query(
                case(
                    (extract("year", func.current_date()) - extract("year", User.birth_date) < 20, "10대"),
                    (extract("year", func.current_date()) - extract("year", User.birth_date) < 30, "20대"),
                    (extract("year", func.current_date()) - extract("year", User.birth_date) < 40, "30대"),
                    (extract("year", func.current_date()) - extract("year", User.birth_date) < 50, "40대"),
                    (extract("year", func.current_date()) - extract("year", User.birth_date) < 60, "50대"),
                    else_="60대 이상",
                ).label("age_group"),
                func.count(User.id).label("count"),
            )
            .filter(User.birth_date.isnot(None))
            .group_by("age_group")
            .all()
        )

        # 성별 통계
        gender_stats = (
            self.db.query(User.gender, func.count(User.id).label("count"))
            .filter(User.gender.isnot(None))
            .group_by(User.gender)
            .all()
        )

        return {
            "overview": {
                "total_users": total_users,
                "new_users_this_month": new_users_this_month,
                "users_with_orders": users_with_orders,
                "conversion_rate": round((users_with_orders / total_users * 100), 2) if total_users > 0 else 0,
            },
            "age_distribution": [{"age_group": stat.age_group, "count": stat.count} for stat in age_stats],
            "gender_distribution": [{"gender": stat.gender, "count": stat.count} for stat in gender_stats],
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """성과 지표"""
        today = date.today()
        this_month_start = today.replace(day=1)

        # 평균 주문 금액
        avg_order_value = self.db.query(func.avg(Order.total_amount)).filter(Order.status == "completed").scalar() or Decimal(
            "0"
        )

        # 주문 완료율
        total_orders = self.db.query(Order).count()
        completed_orders = self.db.query(Order).filter(Order.status == "completed").count()
        completion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0

        # 취소율
        cancelled_orders = self.db.query(Order).filter(Order.status == "cancelled").count()
        cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0

        # 이번 달 목표 대비 실적 (예시: 월 목표 100건)
        monthly_target = 100
        this_month_orders = self.db.query(Order).filter(Order.created_at >= this_month_start).count()
        target_achievement = (this_month_orders / monthly_target * 100) if monthly_target > 0 else 0

        # 고객 생애 가치 (LTV) - 간단한 계산
        avg_customer_orders = self.db.query(func.avg(func.count(Order.id))).group_by(Order.user_id).scalar() or 0

        estimated_ltv = float(avg_order_value) * avg_customer_orders

        return {
            "financial_metrics": {"avg_order_value": float(avg_order_value), "estimated_ltv": estimated_ltv},
            "operational_metrics": {
                "completion_rate": round(completion_rate, 2),
                "cancellation_rate": round(cancellation_rate, 2),
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "cancelled_orders": cancelled_orders,
            },
            "target_metrics": {
                "monthly_target": monthly_target,
                "this_month_orders": this_month_orders,
                "target_achievement": round(target_achievement, 2),
            },
        }

    def get_comprehensive_report(self, period: str = "month") -> Dict[str, Any]:
        """종합 리포트"""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "period": period,
            "overview": self.get_overview_stats(),
            "order_status": self.get_order_status_stats(),
            "daily_trends": self.get_daily_stats(30 if period == "month" else 7),
            "monthly_trends": self.get_monthly_stats(12 if period == "year" else 6),
            "plan_analysis": self.get_plan_stats(),
            "device_analysis": self.get_device_stats(),
            "user_analysis": self.get_user_stats(),
            "performance_metrics": self.get_performance_metrics(),
        }
