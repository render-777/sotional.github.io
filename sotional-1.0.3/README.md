# 소셔널 바둑 클럽 1.0.3

Docker Compose 기반의 웹/DB 구성 바둑 클럽 웹앱입니다. 관리자 계정으로 사용자를 생성하고, 게시판, 일정, 레이팅을 운영할 수 있습니다.

## 구성

- `web`: Flask 기반 웹 애플리케이션
- `db`: MariaDB 11.4 데이터베이스
- `db/init/01-schema.sql`: 최초 실행 시 테이블 생성
- `web/static/uploads`: 게시글 사진 업로드 저장소
- `web/static/img/logo.png`: 로그인 전/후 공통 로고
- `web/static/img/club-hero.png`: 로그인 후 홈 화면 이미지

## 주요 기능

- 계정 생성: 관리자만 가능
- 공지사항: 관리자 글 작성, 사용자 확인
- 자유게시판: 사용자와 관리자 글/사진 작성
- 소셔널 리그: 정기리그, 반기리그, 토너먼트 하위 탭 제공
- 소셔널 뉴스: 관리자 글/사진 작성
- 건의게시판: 사용자와 관리자 건의 글 작성
- 소셔널 일정: 달력 형태 일정 관리, 관리자는 추가/수정/삭제, 사용자는 조회만 가능
- 레이팅: 사용자 계정 생성 시 기본 1000점, 관리자가 대국 결과 등록
- 게시글 검색, 수정, 삭제

## 1.0.3 변경사항

- `소셔널 일정` 탭 접근 시 달력 템플릿에서 발생하던 `day.items` 충돌 오류 수정

## 1.0.2 변경사항

- `소셔널 일정` 메뉴 추가
- 관리자 전용 일정 추가/수정/삭제 기능 추가
- 사용자 조회 전용 달력 화면 추가
- 사용자별 레이팅 컬럼 추가
- Elo 기반 레이팅 알고리즘 추가
  - 낮은 레이팅 사용자가 높은 레이팅 사용자를 이기면 더 크게 상승
  - 높은 레이팅 사용자가 낮은 레이팅 사용자에게 지면 더 크게 하락
- 레이팅 순위표와 최근 대국 기록 추가
- `picture/로그인 후 화면.png`를 로그인 후 홈 화면에 배치
- 기존 1.0.1 데이터가 있어도 앱 시작 시 필요한 테이블과 컬럼을 자동 보강

## 실행 방법

1. Docker Desktop 또는 Docker Engine을 설치하고 실행합니다.
2. 압축을 해제합니다.

   ```bash
   tar -xzf sotional-1.0.3.tar.gz
   cd sotional-1.0.3
   ```

3. `.env.example`을 복사해 `.env`를 만들고 값을 수정합니다.

   ```bash
   cp .env.example .env
   ```

   ```env
   WEB_PORT=8080
   MYSQL_ROOT_PASSWORD=replace-with-local-root-password
   MYSQL_DATABASE=sotional
   MYSQL_USER=sotional_user
   MYSQL_PASSWORD=replace-with-db-password
   SECRET_KEY=replace-with-random-secret-key
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=replace-with-admin-password
   ```

4. 컨테이너를 빌드하고 실행합니다.

   ```bash
   docker compose up -d --build
   ```

5. 브라우저에서 접속합니다.

   ```text
   http://localhost:8080
   ```

   내부망 다른 기기에서는 예를 들어 다음처럼 접속합니다.

   ```text
   http://192.168.0.103:8080
   ```

6. 관리자 계정으로 로그인한 뒤 좌측 `계정 관리`에서 사용자 계정을 생성합니다.

## 레이팅 계산 방식

1. 모든 사용자는 기본 1000점으로 시작합니다.
2. 관리자가 `레이팅` 메뉴에서 승자와 패자를 선택해 결과를 등록합니다.
3. 점수 변동은 Elo 기대 승률 공식으로 계산합니다.

   ```text
   기대승률 = 1 / (1 + 10 ^ ((상대점수 - 내점수) / 400))
   변동점수 = round(32 * (실제결과 - 기대승률))
   ```

4. 예상 밖의 승리일수록 더 많이 오르고, 예상 밖의 패배일수록 더 많이 내려갑니다.

## 운영 명령

로그 확인:

```bash
docker compose logs -f
```

중지:

```bash
docker compose down
```

데이터까지 초기화:

```bash
docker compose down -v
```

로컬 바인드 볼륨까지 완전히 삭제하려면 `db/data` 폴더를 직접 삭제한 뒤 다시 실행합니다.

## GitHub 및 외부 DB 배포

GitHub에는 `.env`, `db/data/`, `web/static/uploads/`를 올리지 않습니다. 이 프로젝트에는 해당 항목을 제외하는 `.gitignore`와 공개 가능한 `.env.example`이 포함되어 있습니다.

외부 DB를 사용할 때는 MySQL/MariaDB 호환 관리형 DB를 권장합니다. 현재 앱은 `PyMySQL` 기반이라 Cloudflare D1에는 그대로 연결할 수 없고, Cloudflare는 Tunnel로 웹앱 공개 URL을 연결하는 용도에 더 적합합니다.

외부 DB만 사용할 때는 `.env`에 `DB_HOST`, `DB_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` 또는 `DATABASE_URL`을 설정한 뒤 다음 명령으로 실행합니다.

```bash
docker compose -f docker-compose.external-db.yml up -d --build
```

자세한 절차는 `DEPLOYMENT.md`를 참고하세요.

## 보안 권장사항

운영 환경에서는 `.env`의 `SECRET_KEY`, DB 비밀번호, `ADMIN_PASSWORD`를 반드시 변경하세요. 기존 관리자 계정은 앱 시작 때 자동으로 비밀번호가 재설정되지 않으며, 강제로 초기 관리자 비밀번호를 다시 적용해야 할 때만 `FORCE_RESET_ADMIN=true`를 임시로 사용하세요.
