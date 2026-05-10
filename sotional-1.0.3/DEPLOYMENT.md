# GitHub and Cloud DB Deployment

## 1. GitHub에 올리기 전 확인

이 프로젝트는 Flask 웹앱과 MariaDB를 Docker Compose로 실행합니다.

GitHub에는 다음 파일을 올립니다.

- `web/`
- `db/init/01-schema.sql`
- `db/config/mariadb/my.cnf`
- `docker-compose.yml`
- `docker-compose.external-db.yml`
- `.env.example`
- `.gitignore`
- `README.md`
- `DEPLOYMENT.md`

GitHub에 올리면 안 되는 파일과 폴더는 `.gitignore`에 등록되어 있습니다.

- `.env`: 비밀번호, 세션 키
- `db/data/`: 로컬 MariaDB 실제 데이터
- `web/static/uploads/`: 사용자가 올린 사진

처음 저장소를 만들 때는 다음 흐름으로 진행합니다.

```bash
cd sotional-1.0.3
copy .env.example .env
```

`.env`의 비밀번호와 `SECRET_KEY`, `ADMIN_PASSWORD`를 바꾼 뒤 실행합니다.

```bash
docker compose up -d --build
```

## 2. 외부 DB 선택

현재 앱은 `PyMySQL`로 MySQL/MariaDB에 연결합니다. 그래서 외부 DB도 MySQL 호환 서비스를 고르는 것이 가장 안전합니다.

추천 선택지는 다음과 같습니다.

- TiDB Cloud: MySQL 호환, 무료 플랜으로 시작하기 쉬움
- PlanetScale: MySQL 호환 서버리스 DB
- Aiven for MySQL/MariaDB: 관리형 DB
- AWS RDS MariaDB/MySQL, Google Cloud SQL, Azure Database for MySQL: 운영용으로 안정적

Cloudflare는 DB 자체로는 이 앱의 MariaDB를 그대로 호스팅하지 않습니다.

- Cloudflare D1은 SQLite 계열이라 현재 코드와 SQL을 그대로 사용할 수 없습니다.
- Cloudflare Pages/Workers는 Flask 컨테이너를 그대로 실행하는 환경이 아닙니다.
- Cloudflare Tunnel은 집/서버에서 실행 중인 웹앱을 안전하게 공개 URL로 연결할 때 사용할 수 있습니다.
- Cloudflare Hyperdrive는 Workers에서 외부 DB 연결을 최적화하는 기능이라, 현재 Flask 앱 단독 배포에는 필수 요소가 아닙니다.

따라서 권장 구조는 `웹앱 컨테이너 + 관리형 MySQL/MariaDB`입니다.

## 3. 외부 DB 초기화

관리형 MySQL/MariaDB에서 데이터베이스와 계정을 만든 뒤, 스키마를 적용합니다.

```bash
mysql -h DB_HOST -P 3306 -u DB_USER -p DB_NAME < db/init/01-schema.sql
```

`mysql` 클라이언트가 없다면 DB 제공사의 SQL 콘솔에 `db/init/01-schema.sql` 내용을 붙여 실행해도 됩니다.

## 4. 외부 DB로 웹앱 실행

`.env`를 다음처럼 설정합니다.

```env
WEB_PORT=8080
SECRET_KEY=긴-랜덤-문자열
UPLOAD_FOLDER=/app/static/uploads

ADMIN_USERNAME=admin
ADMIN_PASSWORD=관리자-초기-비밀번호

MYSQL_DATABASE=DB_NAME
MYSQL_USER=DB_USER
MYSQL_PASSWORD=DB_PASSWORD
DB_HOST=DB_HOST
DB_PORT=3306
DB_SSL_MODE=REQUIRED
```

또는 `DATABASE_URL` 하나로 설정할 수도 있습니다.

```env
DATABASE_URL=mysql://DB_USER:DB_PASSWORD@DB_HOST:3306/DB_NAME
DB_SSL_MODE=REQUIRED
```

외부 DB만 사용할 때는 DB 컨테이너 없이 웹 컨테이너만 실행합니다.

```bash
docker compose -f docker-compose.external-db.yml up -d --build
```

## 5. 기존 컨테이너 DB 데이터 옮기기

이미 로컬 컨테이너에 데이터가 있다면 먼저 덤프합니다.

```bash
docker compose exec db mariadb-dump -u root -p sotional > sotional-backup.sql
```

그 다음 외부 DB에 복원합니다.

```bash
mysql -h DB_HOST -P 3306 -u DB_USER -p DB_NAME < sotional-backup.sql
```

업로드 이미지는 DB가 아니라 `web/static/uploads/`에 저장됩니다. 운영 서버를 바꾸면 이 폴더도 같이 백업하거나, 별도 오브젝트 스토리지로 옮기는 방식이 필요합니다.

## 6. 운영 보안 체크리스트

- `.env`는 절대 GitHub에 커밋하지 않습니다.
- `SECRET_KEY`, DB 비밀번호, `ADMIN_PASSWORD`는 긴 랜덤 값으로 바꿉니다.
- 기본 관리자 계정은 최초 로그인 후 별도 관리자 계정을 만들고 비밀번호를 안전하게 관리합니다.
- 외부 DB는 가능하면 공인 전체 허용 대신 서버 IP만 접속 허용합니다.
- 관리형 DB가 TLS를 요구하면 `DB_SSL_MODE=REQUIRED`를 사용합니다.
- 사용자 업로드 파일은 정기적으로 백업합니다.
