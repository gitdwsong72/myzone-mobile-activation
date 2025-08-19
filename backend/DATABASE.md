# MyZone 데이터베이스 설정 가이드

## 개요

MyZone 핸드폰 개통 서비스의 데이터베이스는 PostgreSQL을 사용하며, SQLAlchemy ORM과 Alembic 마이그레이션을 통해 관리됩니다.

## 데이터베이스 구조

### 주요 테이블

1. **users** - 사용자 정보
2. **plans** - 요금제 정보
3. **devices** - 단말기 정보
4. **numbers** - 전화번호 정보
5. **orders** - 주문 정보
6. **payments** - 결제 정보
7. **admins** - 관리자 계정
8. **order_status_history** - 주문 상태 변경 이력

### ERD 다이어그램

```mermaid
erDiagram
    USERS ||--o{ ORDERS : places
    PLANS ||--o{ ORDERS : selected_in
    DEVICES ||--o{ ORDERS : selected_in
    NUMBERS ||--o{ ORDERS : assigned_to
    ORDERS ||--|| PAYMENTS : has
    ORDERS ||--o{ ORDER_STATUS_HISTORY : tracks
    ADMINS ||--o{ ORDER_STATUS_HISTORY : manages
```

## 설정 방법

### 1. 환경 변수 설정

`.env` 파일에 데이터베이스 연결 정보를 설정하세요:

```env
DATABASE_URL=postgresql://myzone_user:myzone_password@localhost:5432/myzone_db
```

### 2. 데이터베이스 초기화

전체 데이터베이스를 초기화하려면:

```bash
# Docker 환경에서
make init-db

# 또는 직접 실행
python scripts/init_db.py
```

### 3. 마이그레이션만 실행

```bash
# Docker 환경에서
make migrate

# 또는 직접 실행
python -m alembic upgrade head
```

### 4. 시드 데이터만 삽입

```bash
# Docker 환경에서
make seed-db

# 또는 직접 실행
python scripts/seed_db.py
```

## 시드 데이터

### 요금제 (6개)
- **5G 프리미엄** (89,000원) - 무제한 데이터/통화/문자
- **5G 스탠다드** (69,000원) - 100GB 데이터
- **LTE 프리미엄** (55,000원) - 무제한 데이터/통화/문자
- **LTE 스탠다드** (39,000원) - 50GB 데이터
- **데이터 무제한** (49,000원) - 무제한 데이터, 300분 통화
- **통화 무제한** (35,000원) - 10GB 데이터, 무제한 통화

### 단말기 (5개)
- **삼성 갤럭시 S24 Ultra** (1,298,000원)
- **삼성 갤럭시 S24** (898,000원)
- **애플 아이폰 15 Pro Max** (1,550,000원)
- **애플 아이폰 15** (1,150,000원)
- **LG V60 ThinQ** (498,000원)

### 전화번호 (14개)
- **일반 번호** (5개) - 추가 요금 없음
- **연속 번호** (4개) - 50,000~100,000원 추가
- **특별 번호** (5개) - 150,000~300,000원 추가

### 관리자 계정 (3개)
- **admin** / admin123! (슈퍼 관리자)
- **operator1** / operator123! (운영자)
- **operator2** / operator123! (운영자)

## 마이그레이션 관리

### 새 마이그레이션 생성

```bash
python -m alembic revision --autogenerate -m "마이그레이션 설명"
```

### 마이그레이션 히스토리 확인

```bash
python -m alembic history
```

### 특정 버전으로 롤백

```bash
python -m alembic downgrade <revision_id>
```

## 모델 구조

### 기본 모델 (BaseModel)
모든 모델은 `BaseModel`을 상속받아 다음 필드를 자동으로 포함합니다:
- `id` (Primary Key)
- `created_at` (생성 시간)
- `updated_at` (수정 시간)

### 주요 모델 특징

#### User 모델
- 개인정보 암호화 저장 지원
- 본인인증 상태 관리
- 주문과 1:N 관계

#### Order 모델
- 자동 주문번호 생성 (MZ + 날짜 + UUID)
- 총 금액 자동 계산
- 상태 변경 이력 추적

#### Number 모델
- 번호 예약 시스템 (30분 임시 예약)
- 프리미엄 번호 추가 요금 관리
- 패턴 타입별 분류

#### Payment 모델
- PG사 연동 정보 저장
- 환불 처리 지원
- 카드 정보 토큰화 저장

## 성능 최적화

### 인덱스 설정
- 자주 조회되는 컬럼에 인덱스 설정
- 복합 인덱스로 쿼리 성능 향상
- 외래키 자동 인덱싱

### 쿼리 최적화
- N+1 문제 방지를 위한 eager loading
- 페이지네이션 지원
- 필터링 최적화

## 보안 고려사항

### 데이터 암호화
- 개인정보는 AES-256 암호화
- 비밀번호는 bcrypt 해싱
- 카드 정보는 토큰화 저장

### 접근 제어
- 관리자 권한별 접근 제어
- API 레벨에서 데이터 필터링
- 민감 정보 마스킹 처리

## 백업 및 복구

### 정기 백업
```bash
# 데이터베이스 백업
pg_dump myzone_db > backup_$(date +%Y%m%d).sql

# 백업 복구
psql myzone_db < backup_20240112.sql
```

### Docker 볼륨 백업
```bash
# 볼륨 백업
docker run --rm -v myzone_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data

# 볼륨 복구
docker run --rm -v myzone_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## 문제 해결

### 일반적인 문제

1. **마이그레이션 실패**
   - 데이터베이스 연결 확인
   - 권한 문제 확인
   - 기존 데이터와 충돌 확인

2. **시드 데이터 중복**
   - 스크립트는 중복 체크 후 삽입
   - 기존 데이터가 있으면 스킵

3. **성능 문제**
   - 쿼리 실행 계획 확인
   - 인덱스 사용 여부 확인
   - 커넥션 풀 설정 확인

### 로그 확인
```bash
# 데이터베이스 로그 확인
docker-compose logs db

# 백엔드 애플리케이션 로그
docker-compose logs backend
```