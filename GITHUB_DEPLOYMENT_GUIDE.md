# MyZone GitHub 배포 가이드

## 🚀 1단계: GitHub 저장소 생성

### 1.1 GitHub에서 새 저장소 생성
1. GitHub에 로그인
2. "New repository" 클릭
3. 저장소 이름: `myzone-mobile-activation`
4. 설명: `MyZone 핸드폰 개통 서비스 - 온라인 모바일 개통 플랫폼`
5. Public 또는 Private 선택
6. "Create repository" 클릭

### 1.2 로컬 Git 초기화 및 업로드
```bash
# 현재 디렉토리에서 실행
git init
git add .
git commit -m "feat: MyZone 모바일 개통 서비스 초기 구현

- FastAPI 백엔드 완전 구현 (17개 주요 기능)
- React 프론트엔드 완전 구현 (모든 페이지)
- Docker 컨테이너화 및 CI/CD 파이프라인
- 테스트 코드 (백엔드 15개, 프론트엔드 27개, E2E 3개)
- 모니터링 시스템 (Prometheus, Grafana, ELK)
- 보안 강화 및 성능 최적화
- 배포 자동화 스크립트"

git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/myzone-mobile-activation.git
git push -u origin main

# develop 브랜치 생성
git checkout -b develop
git push -u origin develop
```

## 🔧 2단계: GitHub Secrets 설정

### 2.1 자동 설정 (권장)
```bash
# GitHub CLI 설치 (macOS)
brew install gh

# GitHub CLI 로그인
gh auth login

# 자동 Secrets 설정 실행
./scripts/setup-github-secrets.sh
```

### 2.2 수동 설정
GitHub 저장소 → Settings → Secrets and variables → Actions에서 다음 Secrets 추가:

#### 필수 Secrets
- `STAGING_SSH_KEY`: 스테이징 서버 SSH 개인키
- `STAGING_USER`: 스테이징 서버 사용자명
- `STAGING_HOST`: 스테이징 서버 호스트
- `STAGING_URL`: 스테이징 서버 URL

- `PRODUCTION_SSH_KEY`: 프로덕션 서버 SSH 개인키  
- `PRODUCTION_USER`: 프로덕션 서버 사용자명
- `PRODUCTION_HOST`: 프로덕션 서버 호스트
- `PRODUCTION_URL`: 프로덕션 서버 URL

#### 선택사항 Secrets
- `SLACK_WEBHOOK`: 슬랙 알림 웹훅 URL
- `CODECOV_TOKEN`: 코드 커버리지 토큰

## 🖥️ 3단계: 서버 환경 준비

### 3.1 클라우드 서버 생성
#### AWS EC2 (권장)
```bash
# t3.medium 이상 권장 (2 vCPU, 4GB RAM)
# Ubuntu 22.04 LTS
# 보안 그룹: 22(SSH), 80(HTTP), 443(HTTPS), 3000(React), 8000(FastAPI)
```

#### Google Cloud Platform
```bash
# e2-standard-2 이상 권장
# Ubuntu 22.04 LTS
```

#### DigitalOcean
```bash
# Basic Droplet $24/month 이상 권장
# Ubuntu 22.04 LTS
```

### 3.2 서버 초기 설정
```bash
# 서버 접속
ssh ubuntu@your-server-ip

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 설치
sudo apt install git -y

# 프로젝트 클론
sudo mkdir -p /opt/myzone
sudo chown $USER:$USER /opt/myzone
cd /opt/myzone
git clone https://github.com/YOUR_USERNAME/myzone-mobile-activation.git .

# 환경 변수 설정
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 환경 변수 편집 (실제 값으로 수정)
nano .env
nano backend/.env
nano frontend/.env
```

### 3.3 도메인 및 SSL 설정
```bash
# 도메인 구매 후 A 레코드 설정
# 예: myzone.com → 서버 IP
#     staging.myzone.com → 스테이징 서버 IP

# SSL 인증서 자동 설정
./scripts/ssl-setup.sh myzone.com admin@myzone.com
```

## 🚀 4단계: 배포 실행

### 4.1 수동 배포 (첫 배포)
```bash
# 서버에서 실행
cd /opt/myzone

# 프로덕션 배포
./scripts/deploy.sh production

# 또는 통합 관리 도구 사용
./scripts/manage.sh deploy production
```

### 4.2 자동 배포 (CI/CD)
```bash
# 로컬에서 develop 브랜치에 push → 스테이징 자동 배포
git checkout develop
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin develop

# main 브랜치에 merge → 프로덕션 자동 배포
git checkout main
git merge develop
git push origin main
```

## 📊 5단계: 모니터링 시스템 설정

### 5.1 모니터링 스택 시작
```bash
# 서버에서 실행
./scripts/manage.sh monitor start

# 또는 직접 실행
docker-compose -f docker-compose.monitoring.yml up -d
```

### 5.2 모니터링 대시보드 접속
- **Grafana**: https://your-domain.com:3001 (admin/admin123)
- **Prometheus**: https://your-domain.com:9090
- **Kibana**: https://your-domain.com:5601

## 🔍 6단계: 배포 확인

### 6.1 서비스 상태 확인
```bash
# 헬스체크
./scripts/manage.sh health

# 서비스 상태 확인
./scripts/manage.sh status

# 로그 확인
./scripts/manage.sh logs
```

### 6.2 웹사이트 접속 테스트
- **메인 사이트**: https://your-domain.com
- **API 문서**: https://your-domain.com/docs
- **관리자**: https://your-domain.com/admin/login

## 🛠️ 7단계: 운영 관리

### 7.1 일상 운영 명령어
```bash
# 전체 상태 확인
./scripts/manage.sh status

# 백업 실행
./scripts/manage.sh backup

# 로그 확인
./scripts/manage.sh logs [service]

# 서비스 재시작
./scripts/manage.sh restart [service]
```

### 7.2 업데이트 배포
```bash
# 코드 수정 후
git add .
git commit -m "fix: 버그 수정"
git push origin develop  # 스테이징 배포

# 테스트 완료 후
git checkout main
git merge develop
git push origin main     # 프로덕션 배포
```

## 🚨 8단계: 문제 해결

### 8.1 일반적인 문제
```bash
# 컨테이너 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f [service]

# 디스크 공간 정리
./scripts/manage.sh clean

# 데이터베이스 복구
./scripts/disaster-recovery.sh --backup-date 2024-01-15
```

### 8.2 긴급 롤백
```bash
# GitHub Actions에서 수동 실행
# 또는 서버에서 직접 실행
git checkout HEAD~1
./scripts/deploy.sh production --force
```

## 📞 지원 및 문의

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **Wiki**: 상세 문서 및 FAQ
- **Discussions**: 커뮤니티 질문 및 답변

---

## 🎉 배포 완료!

축하합니다! MyZone 모바일 개통 서비스가 성공적으로 배포되었습니다.

### 다음 단계
1. 실제 PG사 연동 설정
2. SMS 발송 서비스 연동
3. 본인인증 API 연동
4. 실제 요금제 및 단말기 데이터 입력
5. 성능 최적화 및 모니터링

### 주요 URL
- **서비스**: https://your-domain.com
- **관리자**: https://your-domain.com/admin
- **API**: https://your-domain.com/api/v1
- **모니터링**: https://your-domain.com:3001