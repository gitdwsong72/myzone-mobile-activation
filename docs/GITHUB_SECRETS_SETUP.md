# GitHub Secrets 설정 가이드

MyZone CI/CD 파이프라인이 정상적으로 작동하려면 다음 GitHub Secrets를 설정해야 합니다.

## 설정 방법

1. GitHub 저장소 페이지로 이동
2. **Settings** 탭 클릭
3. 왼쪽 사이드바에서 **Secrets and variables** → **Actions** 클릭
4. **New repository secret** 버튼 클릭
5. 아래 목록의 각 Secret을 하나씩 추가

## 필수 Secrets

### 🚀 배포 관련 Secrets

#### 스테이징 환경
```
STAGING_SSH_KEY
```
- **설명**: 스테이징 서버 SSH 개인키
- **값 예시**: 
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAFwAAAAdzc2gtcn...
-----END OPENSSH PRIVATE KEY-----
```
- **생성 방법**: `ssh-keygen -t rsa -b 4096 -C "staging@myzone.com"`

```
STAGING_USER
```
- **설명**: 스테이징 서버 사용자명
- **값 예시**: `ubuntu` 또는 `myzone`

```
STAGING_HOST
```
- **설명**: 스테이징 서버 호스트 주소
- **값 예시**: `staging.myzone.com` 또는 `192.168.1.100`

```
STAGING_URL
```
- **설명**: 스테이징 서버 URL (헬스체크용)
- **값 예시**: `https://staging.myzone.com`

#### 프로덕션 환경
```
PRODUCTION_SSH_KEY
```
- **설명**: 프로덕션 서버 SSH 개인키
- **값 예시**: SSH 개인키 전체 내용
- **생성 방법**: `ssh-keygen -t rsa -b 4096 -C "production@myzone.com"`

```
PRODUCTION_USER
```
- **설명**: 프로덕션 서버 사용자명
- **값 예시**: `ubuntu` 또는 `myzone`

```
PRODUCTION_HOST
```
- **설명**: 프로덕션 서버 호스트 주소
- **값 예시**: `myzone.com` 또는 `10.0.1.100`

```
PRODUCTION_URL
```
- **설명**: 프로덕션 서버 URL (헬스체크용)
- **값 예시**: `https://myzone.com`

### 📢 알림 관련 Secrets (선택사항)

```
SLACK_WEBHOOK
```
- **설명**: 슬랙 웹훅 URL (배포 알림용)
- **값 예시**: `https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX`
- **설정 방법**: 
  1. 슬랙 워크스페이스에서 앱 추가
  2. Incoming Webhooks 활성화
  3. 채널 선택 후 웹훅 URL 복사

### 🔐 보안 관련 Secrets (선택사항)

```
CODECOV_TOKEN
```
- **설명**: Codecov 토큰 (코드 커버리지 업로드용)
- **값 예시**: `12345678-1234-1234-1234-123456789012`
- **설정 방법**: Codecov.io에서 저장소 연결 후 토큰 복사

```
SONAR_TOKEN
```
- **설명**: SonarCloud 토큰 (코드 품질 분석용)
- **값 예시**: `sqp_1234567890abcdef1234567890abcdef12345678`

## SSH 키 생성 및 설정

### 1. SSH 키 쌍 생성
```bash
# 스테이징용 키 생성
ssh-keygen -t rsa -b 4096 -C "staging@myzone.com" -f ~/.ssh/myzone_staging

# 프로덕션용 키 생성
ssh-keygen -t rsa -b 4096 -C "production@myzone.com" -f ~/.ssh/myzone_production
```

### 2. 공개키를 서버에 추가
```bash
# 스테이징 서버에 공개키 추가
ssh-copy-id -i ~/.ssh/myzone_staging.pub user@staging.myzone.com

# 프로덕션 서버에 공개키 추가
ssh-copy-id -i ~/.ssh/myzone_production.pub user@myzone.com
```

### 3. 개인키를 GitHub Secrets에 추가
```bash
# 개인키 내용 복사 (스테이징)
cat ~/.ssh/myzone_staging

# 개인키 내용 복사 (프로덕션)
cat ~/.ssh/myzone_production
```

## 환경별 설정 예시

### 개발/테스트 환경
```
STAGING_SSH_KEY=<SSH_PRIVATE_KEY>
STAGING_USER=ubuntu
STAGING_HOST=dev.myzone.com
STAGING_URL=https://dev.myzone.com
SLACK_WEBHOOK=<SLACK_WEBHOOK_URL>
```

### 프로덕션 환경
```
PRODUCTION_SSH_KEY=<SSH_PRIVATE_KEY>
PRODUCTION_USER=myzone
PRODUCTION_HOST=myzone.com
PRODUCTION_URL=https://myzone.com
SLACK_WEBHOOK=<SLACK_WEBHOOK_URL>
```

## 보안 주의사항

### ✅ 해야 할 것
- SSH 키는 각 환경별로 별도 생성
- 정기적으로 SSH 키 교체 (6개월마다)
- 최소 권한 원칙 적용
- 서버 접근 로그 모니터링

### ❌ 하지 말아야 할 것
- 개인키를 코드에 직접 포함
- 같은 SSH 키를 여러 환경에서 재사용
- 패스워드 없는 SSH 키 사용 (프로덕션)
- Secrets를 로그에 출력

## 검증 방법

### SSH 연결 테스트
```bash
# 스테이징 서버 연결 테스트
ssh -i ~/.ssh/myzone_staging user@staging.myzone.com "echo 'Connection successful'"

# 프로덕션 서버 연결 테스트
ssh -i ~/.ssh/myzone_production user@myzone.com "echo 'Connection successful'"
```

### GitHub Actions 테스트
1. 간단한 변경사항을 develop 브랜치에 push
2. Actions 탭에서 워크플로우 실행 확인
3. 스테이징 배포가 성공하는지 확인

## 문제 해결

### SSH 연결 실패
```bash
# SSH 연결 디버그
ssh -vvv -i ~/.ssh/myzone_staging user@staging.myzone.com

# 권한 확인
ls -la ~/.ssh/
chmod 600 ~/.ssh/myzone_staging
chmod 644 ~/.ssh/myzone_staging.pub
```

### GitHub Actions 실패
1. Actions 탭에서 실패한 워크플로우 확인
2. 로그에서 오류 메시지 확인
3. Secrets 값이 올바른지 확인
4. 서버 상태 및 네트워크 연결 확인

## 추가 리소스

- [GitHub Secrets 공식 문서](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [SSH 키 관리 가이드](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [슬랙 웹훅 설정](https://api.slack.com/messaging/webhooks)

---

**⚠️ 중요**: 이 문서의 예시 값들은 실제 운영에서 사용하지 마세요. 실제 환경에 맞는 값으로 교체해야 합니다.