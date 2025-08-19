# 📘 GEMINI.md

## 1. 🧾 프로젝트 규칙

- **데이터베이스**: PostgreSQL
  - 개발 기본 경로: `localhost:5432`
  - 기본 스키마: `public`
  - ORM: SQLAlchemy (Python), Prisma (Node.js 사용 시)

- **기본 언어**: 한국어 (`default: ko`)
- **시간대**: Asia/Seoul (KST)
- **파일 인코딩**: UTF-8
- **코드 포맷터**:  
  - `black`, `isort` (Python)  
  - `prettier`, `eslint` (React/Vue)
- **형상 관리**:  
  - `main` 브랜치로 직접 푸시 금지  
  - Pull Request 기반 병합
- **폴더 구조 규칙**:
  ```
  /src          # 애플리케이션 소스 코드
  /tests        # 유닛 테스트
  /docs         # 문서 (API 명세, 요구사항 등)
  /configs      # 환경 및 설정 파일
  ```

---

## 2. 🎨 코드 스타일 가이드

### 🐍 Python (FastAPI 기반)

- 문법 스타일: [PEP8](https://pep8.org/)
- 코드 포매터: `black`, `isort`
- 타입 힌트 필수
- 함수/메서드: `snake_case`
- 클래스: `PascalCase`
- 파일명: `snake_case.py`
- 주석: 한국어로 명확하게 작성
- TODO/FIXME는 이슈 번호와 함께 작성

```python
def create_user(name: str, age: int) -> User:
    """사용자를 생성합니다."""
    ...
```

### 🌐 Frontend (React / Vue)

- 문법: ES6+ / TypeScript
- 포매터: `prettier`, `eslint`
- 컴포넌트: `PascalCase`
- 훅(Hook): `useXxx` 명명
- 디렉토리 예시:
  ```
  /components
    /Button
      Button.tsx
      Button.test.tsx
  ```

---

## 3. ⚙️ 에이전트 도구 정의

### 🌟 Agent 환경 정보

```yaml
language: ko
default_task_language: ko
default_response_language: ko
timezone: Asia/Seoul
code_style:
  python: PEP8 + black
  js: Prettier
file_structure:
  main: /src
  test: /tests
  docs: /docs
tools:
  - name: shell
    description: bash 명령어 실행
  - name: browser
    description: 웹 검색 도구
  - name: python
    description: Python 인터프리터
  - name: web
    description: 웹 기반 외부 정보 검색
  - name: code_interpreter
    description: 코드 실행 및 디버깅
env:
  DB_TYPE: postgresql
  DB_HOST: localhost
  DB_PORT: 5432
  DB_NAME: app
  DB_USER: user
  DB_PASS: password
  DB_URL: postgresql://user:password@localhost:5432/app
  DEFAULT_LANG: ko
```

### 에이전트 지원 명령어 예시

```bash
# FastAPI API 생성
> Generate FastAPI endpoint to create a new blog post

# 유닛 테스트 작성
> Write pytest for user login logic

# 다국어 기능 추가
> Add i18n logic for Korean and English (default: Korean)

# 문서 자동화
> Generate OpenAPI schema and export to /docs/openapi.json
```

---

## 4. ✅ 테스트 규칙

- 테스트 위치: `/tests/`
- 프레임워크: `pytest`
- 커버리지 기준: **90% 이상**
- 자동화: GitHub Actions 사용  
  `.github/workflows/test.yml` 에 정의

---

## 5. 🌐 다국어(i18n) 규칙

- 기본 언어: `ko`
- 지원 언어: `ko`, `en`
- 구조 예시:
  ```
  /locales
    /ko
      messages.json
    /en
      messages.json
  ```
- 사용 예시 (Python):
```python
from i18n import t

print(t("errors.invalid_token"))  # 자동으로 ko/en 대응
```

---

## 6. 🐳 가상환경(Virtual Environment) 설정

- **Python 환경**: `venv` 또는 `virtualenv` 사용 권장
- **Node 환경**: `nvm`을 이용한 버전 관리 권장

### Python 가상환경 생성 및 실행

```bash
python3 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

---

## 🙋 기타

- 이 문서는 **AI 에이전트(Gemini, Cline 등)** 와 **협업 개발자** 모두를 위한 통합 가이드입니다.
- 변경 시 반드시 PR로 공유하고, 관련 에이전트 구성도 함께 업데이트할 것.
