# 배포 가이드 (Deployment Guide)

이 문서는 MyZone 애플리케이션을 Staging 및 Production 환경에 배포하는 방법을 안내합니다.

## 개요

이 프로젝트는 GitHub Actions를 사용하여 CI/CD 파이프라인이 완벽하게 자동화되어 있습니다. 배포는 특정 브랜치(`develop`, `main`)에 코드를 푸시하면 자동으로 트리거됩니다.

- **Staging 환경 배포**: `develop` 브랜치에 푸시
- **Production 환경 배포**: `main` 브랜치에 푸시

배포는 원격 서버에 SSH로 접속하여 `scripts/deploy.sh` 스크립트를 실행하는 방식으로 동작합니다. 성공적인 배포를 위해서는 사전에 몇 가지 설정이 필요합니다.

## 1. GitHub Repository Secrets 설정

배포 자동화에 필요한 민감한 정보들은 GitHub Repository의 Secrets에 등록해야 합니다.

**Settings > Secrets and variables > Actions** 로 이동하여 다음 Secret들을 등록해주세요.

### Staging 환경
| Secret 이름 | 설명 | 예시 값 |
|---|---|---|
| `STAGING_SSH_KEY` | Staging 서버 접속을 위한 SSH Private Key | `-----BEGIN OPENSSH PRIVATE KEY----- ...` |
| `STAGING_USER` | Staging 서버 접속 유저 이름 | `ubuntu` |
| `STAGING_HOST` | Staging 서버의 IP 주소 또는 도메인 | `1.2.3.4` |
| `STAGING_URL` | Staging 서비스의 Health Check URL | `http://staging.myzone.com` |

### Production 환경
| Secret 이름 | 설명 | 예시 값 |
|---|---|---|
| `PRODUCTION_SSH_KEY` | Production 서버 접속을 위한 SSH Private Key | `-----BEGIN OPENSSH PRIVATE KEY----- ...` |
| `PRODUCTION_USER` | Production 서버 접속 유저 이름 | `ubuntu` |
| `PRODUCTION_HOST` | Production 서버의 IP 주소 또는 도메인 | `5.6.7.8` |
| `PRODUCTION_URL` | Production 서비스의 Health Check URL | `https://myzone.com` |

### 기타
| Secret 이름 | 설명 | 예시 값 |
|---|---|---|
| `SLACK_WEBHOOK` | 배포 알림을 받을 Slack Webhook URL | `https://hooks.slack.com/services/...` |


## 2. 배포 서버 사전 설정

Staging 및 Production 서버에는 배포 스크립트가 정상적으로 동작하기 위해 몇 가지 파일이 미리 준비되어 있어야 합니다.

SSH로 서버에 접속하여 프로젝트 디렉토리(예: `/opt/myzone`)에 다음 파일들을 생성해주세요.

1.  **Staging 서버 (`/opt/myzone`)**
    - `.env.staging` 파일을 생성하고 Staging 환경에 맞는 환경변수를 설정합니다. `.env.example` 파일을 참고하세요.

2.  **Production 서버 (`/opt/myzone`)**
    - `.env.production` 파일을 생성하고 Production 환경에 맞는 환경변수를 설정합니다.
    - `secrets/.env.secrets` 파일: 데이터베이스 암호 등 민감한 정보를 담는 파일입니다.
        - 이 파일이 없으면 `deploy.sh` 스크립트가 실행될 때 `scripts/generate-secrets.sh`를 통해 생성할지 묻습니다. 미리 생성해두는 것을 권장합니다.

## 3. 배포 실행

위의 모든 설정이 완료되었다면, 배포를 진행할 수 있습니다.

- **Staging 배포**: 로컬 컴퓨터에서 `develop` 브랜치에 코드를 푸시합니다.
  ```bash
  git checkout develop
  git push origin develop
  ```
- **Production 배포**: `main` 브랜치로 코드를 병합하고 푸시합니다.
  ```bash
  git checkout main
  git merge develop
  git push origin main
  ```

푸시가 완료되면 GitHub Actions 탭에서 배포 워크플로우가 실행되는 것을 확인할 수 있습니다.
