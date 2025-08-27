# MyZone 핸드폰 개통 서비스

[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/myzone-mobile-activation/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/YOUR_USERNAME/myzone-mobile-activation/actions/workflows/ci-cd.yml)
[![Test Suite](https://github.com/YOUR_USERNAME/myzone-mobile-activation/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/myzone-mobile-activation/actions/workflows/test.yml)
[![GitHub Pages](https://github.com/YOUR_USERNAME/myzone-mobile-activation/actions/workflows/github-pages.yml/badge.svg)](https://github.com/YOUR_USERNAME/myzone-mobile-activation/actions/workflows/github-pages.yml)
[![Docker Hub](https://github.com/YOUR_USERNAME/myzone-mobile-activation/actions/workflows/docker-hub.yml/badge.svg)](https://github.com/YOUR_USERNAME/myzone-mobile-activation/actions/workflows/docker-hub.yml)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/myzone-mobile-activation/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/myzone-mobile-activation)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

MyZone은 고객이 온라인으로 휴대폰 개통 신청을 할 수 있는 통합 플랫폼입니다.

## 기술 스택

### 백엔드
- **FastAPI**: Python 웹 프레임워크
- **PostgreSQL**: 메인 데이터베이스
- **Redis**: 캐싱 및 세션 저장소
- **SQLAlchemy**: ORM
- **Alembic**: 데이터베이스 마이그레이션
- **JWT**: 인증 시스템

### 프론트엔드
- **React 18**: UI 라이브러리
- **TypeScript**: 타입 안전성
- **Redux Toolkit**: 상태 관리
- **React Router**: 라우팅
- **Axios**: HTTP 클라이언트

### 인프라
- **Docker**: 컨테이너화
- **Docker Compose**: 로컬 개발 환경
- **Nginx**: 리버스 프록시 (프로덕션)

## 프로젝트 구조

```
myzone/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 라우터
│   │   ├── core/           # 핵심 설정
│   │   └── main.py         # 애플리케이션 진입점
│   ├── alembic/            # 데이터베이스 마이그레이션
│   ├── requirements.txt    # Python 의존성
│   └── Dockerfile
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # 재사용 가능한 컴포넌트
│   │   ├── pages/          # 페이지 컴포넌트
│   │   ├── services/       # API 서비스
│   │   └── store/          # Redux 스토어
│   ├── package.json
│   └── Dockerfile
├── database/               # 데이터베이스 초기화
├── docker-compose.yml      # 개발 환경
├── docker-compose.prod.yml # 프로덕션 환경
└── README.md
```

## 개발 환경 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd myzone
```

### 2. 환경 변수 설정
```bash
# 루트 디렉토리
cp .env.example .env

# 백엔드
cp backend/.env.example backend/.env

# 프론트엔드
cp frontend/.env.example frontend/.env
```

### 3. Docker Compose로 실행
```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

### 4. 개별 서비스 실행 (선택사항)

#### 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

## 서비스 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 데이터베이스 마이그레이션

```bash
# 백엔드 컨테이너 접속
docker-compose exec backend bash

# 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 적용
alembic upgrade head
```

## 개발 가이드

### API 개발
- FastAPI의 자동 문서화 기능을 활용하세요 (`/docs`)
- Pydantic 모델을 사용하여 요청/응답 검증을 구현하세요
- 적절한 HTTP 상태 코드를 사용하세요

### 프론트엔드 개발
- TypeScript를 활용하여 타입 안전성을 확보하세요
- Redux Toolkit을 사용하여 상태를 관리하세요
- 반응형 디자인을 고려하여 개발하세요

### 보안 고려사항
- 환경 변수에 민감한 정보를 저장하세요
- JWT 토큰의 만료 시간을 적절히 설정하세요
- HTTPS를 사용하여 통신을 암호화하세요

## 테스트

### 전체 테스트 실행
```bash
# 모든 테스트 실행
./run-all-tests.sh

# 백엔드 테스트만 실행
cd backend && python -m pytest

# 프론트엔드 테스트만 실행
cd frontend && npm test

# E2E 테스트 실행
npx playwright test
```

### 테스트 커버리지
```bash
# 백엔드 커버리지
cd backend && python -m pytest --cov=app --cov-report=html

# 프론트엔드 커버리지
cd frontend && npm run test:coverage
```

## 배포 및 운영

### 통합 관리 도구
MyZone은 모든 운영 작업을 위한 통합 관리 스크립트를 제공합니다:

```bash
# 초기 설정
./scripts/manage.sh setup

# 배포
./scripts/manage.sh deploy production

# 헬스체크
./scripts/manage.sh health

# 백업
./scripts/manage.sh backup

# 모니터링 시작
./scripts/manage.sh monitor start

# 전체 상태 확인
./scripts/manage.sh status
```

### 환경별 배포

#### 스테이징 환경
```bash
# 스테이징 배포
./scripts/deploy.sh staging

# 또는 통합 도구 사용
./scripts/manage.sh deploy staging
```

#### 프로덕션 환경
```bash
# 프로덕션 배포 (백업 포함)
./scripts/deploy.sh production

# 또는 통합 도구 사용
./scripts/manage.sh deploy production
```

### SSL 인증서 설정
```bash
# Let's Encrypt 인증서 자동 설정
./scripts/ssl-setup.sh myzone.com admin@myzone.com

# 또는 통합 도구 사용
./scripts/manage.sh ssl myzone.com admin@myzone.com
```

### 모니터링 시스템

#### 모니터링 스택 시작
```bash
# 모니터링 시스템 시작
docker-compose -f docker-compose.monitoring.yml up -d

# 또는 통합 도구 사용
./scripts/manage.sh monitor start
```

#### 모니터링 대시보드
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601
- **AlertManager**: http://localhost:9093

### 백업 및 복구

#### 자동 백업
```bash
# 수동 백업 실행
./scripts/backup.sh

# 또는 통합 도구 사용
./scripts/manage.sh backup
```

#### 재해 복구
```bash
# 특정 날짜 백업으로 복구
./scripts/disaster-recovery.sh --backup-date 2024-01-15

# 특정 파일로 복구
./scripts/disaster-recovery.sh --backup-file /backups/myzone_backup_20240115.sql.gz

# 또는 통합 도구 사용
./scripts/manage.sh restore --backup-date 2024-01-15
```

### CI/CD 파이프라인

GitHub Actions를 통한 자동화된 CI/CD 파이프라인이 구성되어 있습니다:

1. **코드 품질 검사**: ESLint, Prettier, Black, Flake8
2. **보안 스캔**: Trivy, CodeQL, Bandit
3. **단위 테스트**: pytest, Jest
4. **통합 테스트**: E2E 테스트
5. **Docker 이미지 빌드**: 멀티스테이지 빌드
6. **자동 배포**: 스테이징/프로덕션 환경

#### GitHub Secrets 자동 설정
```bash
# 자동 설정 (권장)
./scripts/manage.sh secrets setup

# 수동 설정 가이드 확인
./scripts/manage.sh secrets template

# 설정 검증
./scripts/manage.sh secrets validate
```

#### 필요한 GitHub Secrets
```
# 필수 Secrets
STAGING_SSH_KEY          # 스테이징 서버 SSH 키
STAGING_USER             # 스테이징 서버 사용자
STAGING_HOST             # 스테이징 서버 호스트
STAGING_URL              # 스테이징 서버 URL

PRODUCTION_SSH_KEY       # 프로덕션 서버 SSH 키
PRODUCTION_USER          # 프로덕션 서버 사용자
PRODUCTION_HOST          # 프로덕션 서버 호스트
PRODUCTION_URL           # 프로덕션 서버 URL

# 선택사항 Secrets
SLACK_WEBHOOK            # 슬랙 알림 웹훅 URL
CODECOV_TOKEN            # 코드 커버리지 토큰
```

자세한 설정 방법은 [GitHub Secrets 설정 가이드](docs/GITHUB_SECRETS_SETUP.md)를 참고하세요.

### 로그 관리

#### 로그 확인
```bash
# 전체 로그 확인
./scripts/manage.sh logs

# 특정 서비스 로그 확인
./scripts/manage.sh logs backend
./scripts/manage.sh logs frontend
./scripts/manage.sh logs nginx
```

#### 로그 수집 (ELK Stack)
- **Elasticsearch**: 로그 저장소
- **Logstash**: 로그 처리 파이프라인
- **Kibana**: 로그 시각화
- **Filebeat**: 로그 수집 에이전트

### 성능 모니터링

#### 메트릭 수집
- **Prometheus**: 메트릭 수집 및 저장
- **Node Exporter**: 시스템 메트릭
- **cAdvisor**: 컨테이너 메트릭
- **Custom Metrics**: 애플리케이션 메트릭

#### 알림 설정
- **AlertManager**: 알림 관리
- **Slack 통합**: 실시간 알림
- **이메일 알림**: 중요 이벤트 알림

### 보안 관리

#### SSL/TLS 설정
- Let's Encrypt 자동 인증서 발급
- 자동 갱신 설정
- 보안 헤더 적용

#### 시크릿 관리
```bash
# 시크릿 생성
./scripts/generate-secrets.sh

# 시크릿 파일 위치
secrets/.env.secrets  # 프로덕션 시크릿
```

### 문제 해결

#### 일반적인 문제
1. **컨테이너 시작 실패**: `docker-compose logs [service]`로 로그 확인
2. **데이터베이스 연결 오류**: 환경 변수 및 네트워크 설정 확인
3. **SSL 인증서 오류**: 인증서 만료일 및 도메인 설정 확인

#### 헬스체크
```bash
# 전체 시스템 헬스체크
./scripts/health-check.sh

# 또는 통합 도구 사용
./scripts/manage.sh health
```

#### 시스템 정리
```bash
# 불필요한 파일 및 이미지 정리
./scripts/manage.sh clean
```

## 개발 워크플로우

### 브랜치 전략
- `main`: 프로덕션 브랜치
- `develop`: 개발 브랜치
- `feature/*`: 기능 개발 브랜치
- `hotfix/*`: 긴급 수정 브랜치

### 커밋 메시지 규칙
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 스타일 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드 프로세스 또는 보조 도구 변경
```

### 코드 리뷰 가이드라인
1. 코드 품질 및 일관성 확인
2. 보안 취약점 검토
3. 성능 영향 평가
4. 테스트 커버리지 확인
5. 문서화 상태 점검

## 🚀 GitHub 배포

### 빠른 배포
```bash
# 자동 배포 스크립트 실행
./deploy-to-github.sh -u YOUR_GITHUB_USERNAME

# 또는 수동 배포
git init
git add .
git commit -m "feat: MyZone 모바일 개통 서비스 초기 구현"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/myzone-mobile-activation.git
git push -u origin main
```

### GitHub Pages 배포
프론트엔드는 GitHub Pages를 통해 자동으로 배포됩니다:
- **URL**: https://YOUR_USERNAME.github.io/myzone-mobile-activation
- **자동 배포**: main 브랜치에 push 시 자동 빌드 및 배포

### Docker Hub 배포
Docker 이미지는 자동으로 빌드되어 Docker Hub에 배포됩니다:
```bash
# 이미지 사용
docker pull myzone-backend:latest
docker pull myzone-frontend:latest
```

### CI/CD 파이프라인
- ✅ 코드 품질 검사 (ESLint, Black, Flake8)
- ✅ 보안 스캔 (Trivy, CodeQL, Bandit)
- ✅ 단위 테스트 (pytest, Jest)
- ✅ E2E 테스트 (Playwright)
- ✅ Docker 이미지 빌드
- ✅ 자동 배포 (스테이징/프로덕션)

자세한 배포 가이드는 [GITHUB_DEPLOYMENT_GUIDE.md](GITHUB_DEPLOYMENT_GUIDE.md)를 참고하세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.