import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.database import get_db
from app.services.email_queue_service import email_queue_service
from app.services.verification_service import verification_service

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    def __init__(self):
        self.tasks = []
        self.is_running = False

    async def start_background_tasks(self):
        """백그라운드 태스크 시작"""
        if self.is_running:
            logger.info("백그라운드 태스크가 이미 실행 중입니다.")
            return

        self.is_running = True
        logger.info("백그라운드 태스크 시작")

        # 이메일 큐 처리 태스크
        email_task = asyncio.create_task(self._run_email_queue_processor())
        self.tasks.append(email_task)

        # 만료된 인증번호 정리 태스크
        cleanup_task = asyncio.create_task(self._run_verification_cleanup())
        self.tasks.append(cleanup_task)

        # 임시 파일 정리 태스크
        file_cleanup_task = asyncio.create_task(self._run_file_cleanup())
        self.tasks.append(file_cleanup_task)

        # 스토리지 최적화 태스크
        storage_optimization_task = asyncio.create_task(self._run_storage_optimization())
        self.tasks.append(storage_optimization_task)

        # 시스템 모니터링 태스크
        monitoring_task = asyncio.create_task(self._run_system_monitoring())
        self.tasks.append(monitoring_task)

        # 헬스 모니터링 태스크
        health_task = asyncio.create_task(self._run_health_monitoring())
        self.tasks.append(health_task)

        # 알림 확인 태스크
        alert_task = asyncio.create_task(self._run_alert_check())
        self.tasks.append(alert_task)

        logger.info(f"{len(self.tasks)}개의 백그라운드 태스크가 시작되었습니다.")

    async def stop_background_tasks(self):
        """백그라운드 태스크 중지"""
        if not self.is_running:
            return

        logger.info("백그라운드 태스크 중지 중...")
        self.is_running = False

        # 이메일 큐 처리 중지
        email_queue_service.stop_processing()

        # 모니터링 시스템 중지
        try:
            from app.core.health_check import health_monitor
            from app.core.monitoring import system_monitor

            system_monitor.stop_monitoring()
            health_monitor.stop_monitoring()
        except Exception as e:
            logger.error(f"모니터링 시스템 중지 중 오류: {str(e)}")

        # 모든 태스크 취소
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # 태스크 완료 대기
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        self.tasks.clear()
        logger.info("백그라운드 태스크가 중지되었습니다.")

    async def _run_email_queue_processor(self):
        """이메일 큐 처리 태스크"""
        try:
            logger.info("이메일 큐 처리 태스크 시작")
            await email_queue_service.process_queue()
        except asyncio.CancelledError:
            logger.info("이메일 큐 처리 태스크가 취소되었습니다.")
        except Exception as e:
            logger.error(f"이메일 큐 처리 태스크 오류: {str(e)}")

    async def _run_verification_cleanup(self):
        """만료된 인증번호 정리 태스크"""
        try:
            logger.info("인증번호 정리 태스크 시작")

            while self.is_running:
                try:
                    # 10분마다 만료된 인증번호 정리
                    db = next(get_db())
                    cleaned_count = verification_service.cleanup_expired_codes(db)

                    if cleaned_count > 0:
                        logger.info(f"만료된 인증번호 {cleaned_count}개 정리 완료")

                    db.close()

                except Exception as e:
                    logger.error(f"인증번호 정리 중 오류: {str(e)}")

                # 10분 대기
                await asyncio.sleep(600)

        except asyncio.CancelledError:
            logger.info("인증번호 정리 태스크가 취소되었습니다.")
        except Exception as e:
            logger.error(f"인증번호 정리 태스크 오류: {str(e)}")

    async def _run_file_cleanup(self):
        """임시 파일 정리 태스크"""
        try:
            logger.info("파일 정리 태스크 시작")

            while self.is_running:
                try:
                    # 1시간마다 임시 파일 정리
                    from app.services.file_service import file_service

                    cleaned_count = await file_service.cleanup_temp_files()

                    if cleaned_count > 0:
                        logger.info(f"임시 파일 {cleaned_count}개 정리 완료")

                except Exception as e:
                    logger.error(f"파일 정리 중 오류: {str(e)}")

                # 1시간 대기
                await asyncio.sleep(3600)

        except asyncio.CancelledError:
            logger.info("파일 정리 태스크가 취소되었습니다.")
        except Exception as e:
            logger.error(f"파일 정리 태스크 오류: {str(e)}")

    async def _run_storage_optimization(self):
        """스토리지 최적화 태스크"""
        try:
            logger.info("스토리지 최적화 태스크 시작")

            while self.is_running:
                try:
                    # 24시간마다 스토리지 최적화 수행
                    from app.services.storage_service import storage_service

                    # 스토리지 사용량 확인
                    usage = storage_service.get_storage_usage()

                    # 사용량이 80% 이상이면 최적화 수행
                    if usage.get("usage_percentage", 0) > 80:
                        logger.warning(f"스토리지 사용량이 {usage['usage_percentage']}%입니다. 최적화를 수행합니다.")
                        optimization_result = storage_service.optimize_storage()
                        logger.info(f"스토리지 최적화 완료: {optimization_result}")

                except Exception as e:
                    logger.error(f"스토리지 최적화 중 오류: {str(e)}")

                # 24시간 대기
                await asyncio.sleep(86400)

        except asyncio.CancelledError:
            logger.info("스토리지 최적화 태스크가 취소되었습니다.")
        except Exception as e:
            logger.error(f"스토리지 최적화 태스크 오류: {str(e)}")

    async def _run_system_monitoring(self):
        """시스템 모니터링 태스크"""
        try:
            logger.info("시스템 모니터링 태스크 시작")
            from app.core.monitoring import system_monitor

            await system_monitor.start_monitoring()
        except asyncio.CancelledError:
            logger.info("시스템 모니터링 태스크가 취소되었습니다.")
        except Exception as e:
            logger.error(f"시스템 모니터링 태스크 오류: {str(e)}")

    async def _run_health_monitoring(self):
        """헬스 모니터링 태스크"""
        try:
            logger.info("헬스 모니터링 태스크 시작")
            from app.core.health_check import health_monitor

            await health_monitor.start_monitoring()
        except asyncio.CancelledError:
            logger.info("헬스 모니터링 태스크가 취소되었습니다.")
        except Exception as e:
            logger.error(f"헬스 모니터링 태스크 오류: {str(e)}")

    async def _run_alert_check(self):
        """알림 확인 태스크"""
        try:
            logger.info("알림 확인 태스크 시작")
            from app.core.monitoring import alert_manager, metrics_collector

            while self.is_running:
                try:
                    alert_manager.check_alerts(metrics_collector)
                except Exception as e:
                    logger.error(f"알림 확인 중 오류: {str(e)}")

                # 5분마다 확인
                await asyncio.sleep(300)

        except asyncio.CancelledError:
            logger.info("알림 확인 태스크가 취소되었습니다.")
        except Exception as e:
            logger.error(f"알림 확인 태스크 오류: {str(e)}")


# 전역 백그라운드 태스크 매니저
background_task_manager = BackgroundTaskManager()


@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None, None]:
    """FastAPI 애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("애플리케이션 시작")
    await background_task_manager.start_background_tasks()

    yield

    # 종료 시
    logger.info("애플리케이션 종료")
    await background_task_manager.stop_background_tasks()
