# MyZone 개발 편의 명령어

.PHONY: help build up down logs clean test

# 기본 명령어 도움말
help:
	@echo "MyZone 개발 명령어:"
	@echo "  make build     - Docker 이미지 빌드"
	@echo "  make up        - 개발 환경 시작"
	@echo "  make down      - 개발 환경 중지"
	@echo "  make logs      - 로그 확인"
	@echo "  make clean     - 컨테이너 및 볼륨 정리"
	@echo "  make test      - 테스트 실행"
	@echo "  make migrate   - 데이터베이스 마이그레이션"
	@echo "  make init-db   - 데이터베이스 초기화 (테이블 생성 + 시드 데이터)"
	@echo "  make seed-db   - 시드 데이터만 삽입"

# Docker 이미지 빌드
build:
	docker-compose build

# 개발 환경 시작
up:
	docker-compose up -d
	@echo "서비스가 시작되었습니다:"
	@echo "  프론트엔드: http://localhost:3000"
	@echo "  백엔드 API: http://localhost:8000"
	@echo "  API 문서: http://localhost:8000/docs"

# 개발 환경 중지
down:
	docker-compose down

# 로그 확인
logs:
	docker-compose logs -f

# 컨테이너 및 볼륨 정리
clean:
	docker-compose down -v
	docker system prune -f

# 테스트 실행
test:
	docker-compose exec backend pytest
	docker-compose exec frontend npm test

# 데이터베이스 마이그레이션
migrate:
	docker-compose exec backend python -m alembic upgrade head

# 데이터베이스 초기화 (테이블 생성 + 시드 데이터)
init-db:
	docker-compose exec backend python scripts/init_db.py

# 시드 데이터 삽입
seed-db:
	docker-compose exec backend python scripts/seed_db.py

# 프로덕션 환경 시작
prod-up:
	docker-compose -f docker-compose.prod.yml up -d

# 프로덕션 환경 중지
prod-down:
	docker-compose -f docker-compose.prod.yml down