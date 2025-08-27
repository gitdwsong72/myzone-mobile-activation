# 🔧 GitHub Pages 배포 문제 해결 가이드

## 📊 현재 상황 (2025-08-27 14:55 KST)

### ✅ 성공한 부분
- React 앱 빌드 성공 ✅
- 하이브리드 구조 생성 완료 ✅
- 랜딩 페이지 정상 작동 ✅ (https://gitdwsong72.github.io/myzone-mobile-activation/)
- GitHub Actions 테스트 워크플로우 수정 완료 ✅

### ❌ 문제 상황
- React 앱 접근 불가 ❌ (https://gitdwsong72.github.io/myzone-mobile-activation/app/)
- 404 오류 지속 발생
- GitHub Pages 설정 문제 의심

## 🔍 문제 분석

### 1. GitHub Pages 설정 확인 필요
현재 GitHub Pages가 다음 중 어떤 설정으로 되어 있는지 확인이 필요합니다:

1. **gh-pages 브랜치에서 배포** (GitHub Actions 사용)
2. **main 브랜치 루트에서 배포**
3. **main 브랜치 docs 폴더에서 배포** ← 현재 예상 설정

### 2. 가능한 원인들
1. **GitHub Pages 소스 설정 불일치**
   - 설정: main 브랜치 docs 폴더
   - 실제: gh-pages 브랜치 또는 다른 설정

2. **GitHub Actions 충돌**
   - peaceiris/actions-gh-pages가 gh-pages 브랜치에 배포
   - GitHub Pages 설정과 불일치

3. **파일 경로 문제**
   - docs/app/ 구조가 GitHub Pages에서 인식되지 않음
   - 권한 또는 인덱싱 문제

## 🛠️ 해결 방안

### 방안 1: GitHub 저장소 설정 확인 및 수정
**GitHub 웹사이트에서 직접 확인 필요:**

1. GitHub 저장소 → Settings → Pages
2. Source 설정 확인:
   - **Deploy from a branch** 선택
   - **Branch: main** 선택
   - **Folder: /docs** 선택
3. 설정 저장 후 5-10분 대기

### 방안 2: 루트 배포로 변경
```bash
# docs 폴더 내용을 루트로 이동
cp -r docs/* .
git add .
git commit -m "Move to root deployment"
git push origin main
```

### 방안 3: gh-pages 브랜치 배포 활성화
```yaml
# .github/workflows/github-pages.yml 수정
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs
    publish_branch: gh-pages  # gh-pages 브랜치에 배포
```

### 방안 4: 단순 구조로 변경
```bash
# React 앱을 루트에 직접 배치
cp -r frontend/build/* docs/
# 랜딩 페이지를 about.html로 변경
mv docs/index.html docs/about.html
cp frontend/build/index.html docs/index.html
```

## 🎯 권장 해결 순서

### 1단계: GitHub Pages 설정 확인 (즉시)
- GitHub 웹사이트에서 Pages 설정 확인
- Source가 "main 브랜치 docs 폴더"로 설정되어 있는지 확인

### 2단계: 설정이 올바른 경우 (5분)
```bash
# 캐시 무효화를 위한 더미 커밋
echo "<!-- Updated: $(date) -->" >> docs/app/index.html
git add docs/app/index.html
git commit -m "Cache bust: Update timestamp"
git push origin main
```

### 3단계: 여전히 문제가 있는 경우 (10분)
- 단순 구조로 변경 (방안 4)
- React 앱을 루트에 직접 배치

### 4단계: 최종 해결책 (15분)
- 새로운 저장소 생성 후 이전
- 또는 Netlify/Vercel 등 다른 호스팅 서비스 사용

## 📋 체크리스트

### GitHub Pages 설정 확인
- [ ] Repository → Settings → Pages 접근
- [ ] Source: Deploy from a branch 선택됨
- [ ] Branch: main 선택됨
- [ ] Folder: /docs 선택됨
- [ ] Custom domain 설정 없음 확인

### 파일 구조 확인
- [x] docs/index.html 존재 (랜딩 페이지)
- [x] docs/app/index.html 존재 (React 앱)
- [x] docs/404.html 존재 (SPA 라우팅)
- [x] docs/app/static/ 폴더 존재

### 테스트 확인
- [x] 랜딩 페이지 접근 가능
- [ ] React 앱 접근 가능
- [ ] SPA 라우팅 작동
- [ ] 모든 정적 리소스 로딩

## 🚨 긴급 해결책

만약 빠른 해결이 필요하다면:

1. **Netlify 배포** (5분 내 해결)
   - Netlify에 GitHub 저장소 연결
   - Build command: `cd frontend && npm run build:minimal`
   - Publish directory: `frontend/build`

2. **Vercel 배포** (5분 내 해결)
   - Vercel에 GitHub 저장소 연결
   - Framework: React 선택
   - Root directory: `frontend`

## 📞 다음 단계

1. **즉시**: GitHub Pages 설정 확인
2. **5분 후**: 캐시 무효화 시도
3. **10분 후**: 단순 구조로 변경
4. **15분 후**: 대안 호스팅 서비스 고려

---

**작성 시간**: 2025-08-27 14:55 KST  
**우선순위**: 🔥 긴급  
**예상 해결 시간**: 5-15분