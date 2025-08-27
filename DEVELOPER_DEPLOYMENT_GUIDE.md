# MyZone GitHub Pages 배포 가이드 (개발자용)

## 📋 목차
1. [개요](#개요)
2. [사전 요구사항](#사전-요구사항)
3. [GitHub Pages 설정](#github-pages-설정)
4. [자동 배포 설정](#자동-배포-설정)
5. [배포 구조](#배포-구조)
6. [환경 설정](#환경-설정)
7. [빌드 및 배포 프로세스](#빌드-및-배포-프로세스)
8. [문제 해결](#문제-해결)
9. [성능 최적화](#성능-최적화)
10. [모니터링 및 유지보수](#모니터링-및-유지보수)

## 개요

MyZone React 앱을 GitHub Pages에 배포하여 사용자가 실제 서비스를 체험할 수 있도록 하는 시스템입니다. 기존 정적 HTML 랜딩 페이지와 React 앱을 모두 제공하는 하이브리드 구조로 구성되어 있습니다.

### 🎯 배포 목표
- React 앱의 GitHub Pages 자동 배포
- SPA 라우팅 지원
- 데모 모드 기능 제공
- 하이브리드 구조 (랜딩 페이지 + React 앱)
- CI/CD 파이프라인 구축

## 사전 요구사항

### 필수 도구
- **Node.js**: 18.0 이상
- **npm**: 8.0 이상
- **Git**: 최신 버전
- **GitHub 계정**: 저장소 관리 권한

### 권한 설정
```bash
# GitHub CLI 설치 및 로그인 (선택사항)
gh auth login

# 저장소 클론
git clone https://github.com/YOUR_USERNAME/myzone-mobile-activation.git
cd myzone-mobile-activation
```

## GitHub Pages 설정

### 1. 저장소 설정
1. GitHub 저장소로 이동
2. **Settings** → **Pages** 메뉴 선택
3. **Source**: Deploy from a branch 선택
4. **Branch**: `main` 선택
5. **Folder**: `/ (root)` 선택

### 2. 도메인 설정 (선택사항)
```bash
# 커스텀 도메인 사용 시
echo "your-domain.com" > frontend/public/CNAME
```

### 3. 저장소 권한 확인
- **Actions** 권한: Read and write permissions
- **Pages** 권한: GitHub Actions 배포 허용

## 자동 배포 설정

### GitHub Actions 워크플로우
현재 프로젝트에는 `.github/workflows/github-pages.yml` 파일이 설정되어 있습니다:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: Build React app
      run: |
        cd frontend
        npm run build
        
    - name: Setup GitHub Pages structure
      run: |
        # 기존 docs 디렉토리 백업
        if [ -d "docs" ]; then
          cp -r docs docs_backup
        fi
        
        # React 빌드 결과를 docs/app으로 복사
        mkdir -p docs/app
        cp -r frontend/build/* docs/app/
        
        # 랜딩 페이지 복원 (있는 경우)
        if [ -f "docs_backup/index.html" ]; then
          cp docs_backup/index.html docs/
        fi
        
        # 기타 정적 파일들 복원
        if [ -d "docs_backup" ]; then
          find docs_backup -name "*.html" -not -name "index.html" -exec cp {} docs/ \;
          if [ -d "docs_backup/assets" ]; then
            cp -r docs_backup/assets docs/
          fi
        fi
        
    - name: Deploy to GitHub Pages
      uses: peaceiris/actions-gh-pages@v3
      if: github.ref == 'refs/heads/main'
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./docs
        cname: # 커스텀 도메인이 있는 경우 설정
```

### 워크플로우 트리거
- **자동 트리거**: main 브랜치에 push 시
- **수동 트리거**: GitHub Actions 탭에서 수동 실행 가능

## 배포 구조

### 파일 구조
```
docs/ (GitHub Pages 소스)
├── index.html              # 랜딩 페이지
├── deployment-status.html  # 배포 상태 페이지
├── app/                    # React 앱
│   ├── index.html         # React 앱 진입점
│   ├── static/
│   │   ├── css/          # CSS 파일들
│   │   ├── js/           # JavaScript 번들
│   │   └── media/        # 이미지, 폰트 등
│   ├── manifest.json     # PWA 매니페스트
│   ├── 404.html         # SPA 라우팅 지원
│   └── sw.js            # Service Worker
└── assets/              # 공통 리소스
    ├── images/
    └── icons/
```

### URL 구조
- **랜딩 페이지**: `https://username.github.io/myzone-mobile-activation/`
- **React 앱**: `https://username.github.io/myzone-mobile-activation/app/`
- **API 문서**: `https://username.github.io/myzone-mobile-activation/docs/`

## 환경 설정

### 1. React 앱 환경 변수
`frontend/.env.production` 파일 생성:

```bash
# GitHub Pages 배포용 환경 변수
PUBLIC_URL=/myzone-mobile-activation/app
REACT_APP_API_URL=https://myzone-backend-production.up.railway.app/api/v1
REACT_APP_ENVIRONMENT=demo
REACT_APP_DEMO_MODE=true
GENERATE_SOURCEMAP=false
REACT_APP_BASENAME=/myzone-mobile-activation/app
```

### 2. package.json 설정
`frontend/package.json`에 homepage 필드 추가:

```json
{
  "name": "myzone-frontend",
  "homepage": "/myzone-mobile-activation/app",
  "scripts": {
    "build": "react-scripts build",
    "build:github": "REACT_APP_BASENAME=/myzone-mobile-activation/app npm run build"
  }
}
```

### 3. React Router 설정
`frontend/src/App.tsx`에서 basename 설정:

```typescript
import { BrowserRouter } from 'react-router-dom';

function App() {
  const basename = process.env.REACT_APP_BASENAME || '/';
  
  return (
    <BrowserRouter basename={basename}>
      {/* 라우트 설정 */}
    </BrowserRouter>
  );
}
```

## 빌드 및 배포 프로세스

### 로컬 빌드 테스트
```bash
# 프론트엔드 디렉토리로 이동
cd frontend

# 의존성 설치
npm install

# 프로덕션 빌드
npm run build

# 빌드 결과 확인
ls -la build/

# 로컬 서버로 테스트
npx serve -s build -l 3000
```

### 수동 배포
```bash
# 1. React 앱 빌드
cd frontend
npm run build

# 2. docs 디렉토리 구조 생성
cd ..
mkdir -p docs/app
cp -r frontend/build/* docs/app/

# 3. 404.html 생성 (SPA 라우팅 지원)
cat > docs/app/404.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>MyZone Mobile Activation</title>
  <script type="text/javascript">
    var pathSegmentsToKeep = 1;
    var l = window.location;
    l.replace(
      l.protocol + '//' + l.hostname + (l.port ? ':' + l.port : '') +
      l.pathname.split('/').slice(0, 1 + pathSegmentsToKeep).join('/') + 
      '/?/' +
      l.pathname.slice(1).split('/').slice(pathSegmentsToKeep).join('/').replace(/&/g, '~and~') +
      (l.search ? '&' + l.search.slice(1).replace(/&/g, '~and~') : '') +
      l.hash
    );
  </script>
</head>
<body></body>
</html>
EOF

# 4. Git 커밋 및 푸시
git add .
git commit -m "deploy: Update GitHub Pages deployment"
git push origin main
```

### 자동 배포 확인
```bash
# GitHub Actions 상태 확인
gh run list --workflow=github-pages.yml

# 특정 실행 로그 확인
gh run view [RUN_ID] --log
```

## 문제 해결

### 일반적인 문제들

#### 1. 빌드 실패
```bash
# 캐시 클리어 후 재시도
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### 2. 라우팅 문제 (404 오류)
- `404.html` 파일이 올바르게 생성되었는지 확인
- `basename` 설정이 올바른지 확인
- 브라우저 캐시 클리어

#### 3. 환경 변수 문제
```bash
# 환경 변수 확인
cd frontend
npm run build 2>&1 | grep REACT_APP

# .env.production 파일 확인
cat .env.production
```

#### 4. GitHub Actions 권한 문제
- 저장소 Settings → Actions → General에서 권한 확인
- `GITHUB_TOKEN` 권한이 충분한지 확인

### 디버깅 도구

#### 빌드 분석
```bash
# 번들 크기 분석
cd frontend
npm install --save-dev webpack-bundle-analyzer
npm run build
npx webpack-bundle-analyzer build/static/js/*.js
```

#### 네트워크 문제 진단
```bash
# DNS 확인
nslookup username.github.io

# 연결 테스트
curl -I https://username.github.io/myzone-mobile-activation/
```

## 성능 최적화

### 빌드 최적화
```bash
# 1. 의존성 최적화
cd frontend
npm audit fix
npm update

# 2. 번들 크기 최적화
# package.json에 추가
{
  "scripts": {
    "analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js"
  }
}
```

### 캐싱 전략
```javascript
// frontend/public/sw.js - Service Worker 설정
const CACHE_NAME = 'myzone-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});
```

### GitHub Actions 최적화
```yaml
# 캐시 설정 최적화
- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: |
      frontend/node_modules
      ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('frontend/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

## 모니터링 및 유지보수

### 배포 상태 모니터링
```bash
# 배포 상태 확인 스크립트
#!/bin/bash
# scripts/check-deployment.sh

URL="https://username.github.io/myzone-mobile-activation"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $STATUS -eq 200 ]; then
  echo "✅ 배포 성공: $URL"
else
  echo "❌ 배포 실패: HTTP $STATUS"
  exit 1
fi
```

### 자동 헬스체크
```yaml
# .github/workflows/health-check.yml
name: Health Check

on:
  schedule:
    - cron: '0 */6 * * *'  # 6시간마다 실행

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
    - name: Check site availability
      run: |
        curl -f https://username.github.io/myzone-mobile-activation/ || exit 1
        curl -f https://username.github.io/myzone-mobile-activation/app/ || exit 1
```

### 로그 분석
```bash
# GitHub Actions 로그 분석
gh run list --workflow=github-pages.yml --json status,conclusion,createdAt

# 실패한 배포 분석
gh run list --workflow=github-pages.yml --status=failure
```

### 정기 업데이트 체크리스트
- [ ] 의존성 보안 업데이트 확인
- [ ] React 버전 업그레이드 검토
- [ ] GitHub Actions 워크플로우 최적화
- [ ] 성능 메트릭 분석
- [ ] 사용자 피드백 반영

## 고급 설정

### 커스텀 도메인 설정
```bash
# 1. DNS 설정 (도메인 제공업체에서)
# A 레코드: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
# CNAME 레코드: username.github.io

# 2. CNAME 파일 생성
echo "your-domain.com" > frontend/public/CNAME

# 3. GitHub Pages 설정에서 도메인 확인
```

### SSL 인증서 자동 갱신
GitHub Pages는 Let's Encrypt SSL 인증서를 자동으로 제공하고 갱신합니다.

### CDN 설정 (선택사항)
```javascript
// 외부 CDN 사용 시 환경 변수 설정
REACT_APP_CDN_URL=https://cdn.your-domain.com
```

## 보안 고려사항

### 환경 변수 보안
- 클라이언트에 노출되는 변수만 `REACT_APP_` 접두사 사용
- API 키 등 민감 정보는 백엔드에서 처리
- 데모 모드임을 명시적으로 표시

### CORS 설정
```javascript
// 백엔드 CORS 설정 예시
const allowedOrigins = [
  'https://username.github.io',
  'http://localhost:3000'
];
```

## 문서 업데이트

### README.md 업데이트
배포 관련 정보를 README.md에 추가하여 다른 개발자들이 쉽게 이해할 수 있도록 합니다.

### 변경 로그 관리
```markdown
# CHANGELOG.md
## [1.0.0] - 2024-01-15
### Added
- GitHub Pages 자동 배포 설정
- 데모 모드 기능 구현
- SPA 라우팅 지원

### Changed
- React Router basename 설정 업데이트
- 환경 변수 구조 개선

### Fixed
- 404 페이지 리다이렉트 문제 해결
```

---

> 💡 **추가 도움이 필요하신가요?**  
> 배포 과정에서 문제가 발생하면 GitHub Issues를 통해 문의해주세요.  
> 더 자세한 정보는 [GitHub Pages 공식 문서](https://docs.github.com/en/pages)를 참고하세요.