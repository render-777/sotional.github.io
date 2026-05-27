import json
import mimetypes
import os
import time
from calendar import Calendar, month_name
from datetime import date, datetime
from functools import wraps
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import uuid4

import pymysql
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sotional-dev-secret")

UPLOAD_FOLDER = Path(os.environ.get("UPLOAD_FOLDER", "/app/static/uploads"))
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
DEFAULT_RATING = 1000
RATING_K_FACTOR = 32
SHEET_TYPES = {
    "league": "리그전",
    "tournament": "토너먼트",
    "team": "팀전",
    "match": "대항전",
}
TOURNAMENT_SIZES = {
    "4": "4강",
    "8": "8강",
    "16": "16강",
}
RATING_SEED_FLAG = "sotional_rating_seed_2026_1_5_v1"
RATING_SEED_YEAR = 2026
RATING_SEED_MATCHES = [
    (1, 1, "소강우", "이성수"),
    (1, 2, "송현진", "김효정"),
    (1, 2, "송현진", "황세종"),
    (1, 2, "김효정", "송현진"),
    (1, 2, "송현진", "강민구"),
    (1, 3, "문국현", "이호용"),
    (1, 3, "양동일", "송현진"),
    (1, 3, "양동일", "최준민"),
    (1, 6, "김민준", "송현진"),
    (1, 7, "김장수", "강민구"),
    (1, 7, "김장수", "강민구"),
    (1, 9, "권재형", "이장현"),
    (1, 9, "신상준", "권재형"),
    (1, 10, "김장수", "이장현"),
    (1, 10, "이성수", "강민구"),
    (1, 10, "양동일", "최준민"),
    (1, 11, "소강우", "권재형"),
    (1, 11, "이성수", "권재형"),
    (1, 11, "이성수", "권재형"),
    (1, 12, "김시환", "김장수"),
    (1, 13, "권재형", "이장현"),
    (1, 13, "김근영", "권재형"),
    (1, 13, "소강우", "권재형"),
    (1, 15, "김민준", "권재형"),
    (1, 18, "강민구", "소강우"),
    (1, 18, "김시환", "강민구"),
    (1, 18, "김시환", "문국현"),
    (1, 20, "최준민", "송현진"),
    (1, 20, "이성수", "권재형"),
    (1, 22, "권재형", "김장수"),
    (1, 22, "김장수", "권재형"),
    (1, 26, "최준민", "이장현"),
    (1, 27, "소강우", "김장수"),
    (1, 31, "소강우", "이성수"),
    (1, 31, "김근영", "김태세"),
    (2, 1, "이성수", "이호용"),
    (2, 1, "양동일", "소강우"),
    (2, 2, "김근영", "권재형"),
    (2, 3, "양동일", "이성수"),
    (2, 3, "양동일", "김장수"),
    (2, 3, "강민구", "이성수"),
    (2, 3, "이성수", "강민구"),
    (2, 6, "송현진", "소강우"),
    (2, 7, "김근영", "송현진"),
    (2, 10, "소강우", "김민준"),
    (2, 13, "신상준", "이성수"),
    (2, 13, "장윤정", "이성수"),
    (2, 13, "최준민", "김장수"),
    (2, 13, "김시환", "이장현"),
    (2, 13, "김시환", "김장수"),
    (2, 14, "김근영", "최준민"),
    (2, 14, "김시환", "송현진"),
    (2, 14, "김시환", "신상준"),
    (2, 14, "김시환", "장혜민"),
    (2, 15, "송현진", "이호용"),
    (2, 15, "권재형", "송현진"),
    (2, 15, "양동일", "권재형"),
    (2, 15, "김시환", "송현진"),
    (2, 16, "양동일", "송현진"),
    (2, 16, "김시환", "김태세"),
    (2, 16, "최준민", "신상준"),
    (2, 16, "송현진", "이호용"),
    (2, 16, "김시환", "송현진"),
    (2, 18, "김민준", "장혜민"),
    (2, 18, "송현진", "이장현"),
    (2, 18, "송현진", "이장현"),
    (2, 18, "송현진", "장혜민"),
    (2, 18, "양동일", "임경호"),
    (2, 20, "송현진", "이호용"),
    (2, 20, "이성수", "장윤정"),
    (2, 20, "이성수", "이장현"),
    (2, 20, "이장현", "이성수"),
    (2, 21, "이성수", "이호용"),
    (2, 21, "양동일", "소강우"),
    (2, 21, "장혜민", "송현진"),
    (2, 21, "장혜민", "소강우"),
    (2, 21, "소강우", "이성수"),
    (2, 21, "송현진", "이성수"),
    (2, 21, "이성수", "장혜민"),
    (2, 22, "송현진", "소강우"),
    (2, 22, "최준민", "송현진"),
    (2, 22, "김시환", "김장수"),
    (2, 22, "양동일", "김시환"),
    (2, 24, "김시환", "송현진"),
    (2, 24, "김시환", "송현진"),
    (2, 26, "최준민", "양동일"),
    (2, 27, "이성수", "강민구"),
    (3, 1, "최준민", "강민구"),
    (3, 1, "강민구", "송현진"),
    (3, 1, "이성수", "송현진"),
    (3, 2, "박지웅", "최준민"),
    (3, 8, "권재형", "김장수"),
    (3, 9, "양동일", "권재형"),
    (3, 12, "송현진", "강민구"),
    (3, 14, "김시환", "이성수"),
    (3, 14, "신상준", "권재형"),
    (3, 15, "김시환", "송현진"),
    (3, 16, "양동일", "장혜민"),
    (3, 16, "양동일", "김장수"),
    (3, 19, "강민구", "김민준"),
    (3, 19, "양동일", "강민구"),
    (3, 20, "김민준", "이호용"),
    (3, 27, "송현진", "이호용"),
    (3, 27, "김태세", "권재형"),
    (3, 24, "강민구", "이성수"),
    (4, 1, "김장수", "양동일"),
    (4, 5, "이성수", "소강우"),
    (4, 9, "이호용", "권재형"),
    (4, 10, "장윤정", "김민준"),
    (4, 10, "김민준", "장혜민"),
    (4, 10, "양동일", "권재형"),
    (4, 10, "권재형", "소강우"),
    (4, 10, "김시환", "장혜민"),
    (4, 10, "이성수", "장혜민"),
    (4, 10, "이성수", "장윤정"),
    (4, 10, "양동일", "김근영"),
    (4, 13, "김시환", "강민구"),
    (4, 13, "김시환", "강민구"),
    (4, 15, "황인욱", "강민구"),
    (4, 16, "장윤정", "양동일"),
    (4, 20, "강민구", "장윤정"),
    (4, 20, "장혜민", "장윤정"),
    (5, 1, "이호용", "소강우"),
    (5, 3, "양동일", "소강우"),
    (5, 3, "양동일", "소강우"),
    (5, 3, "박지웅", "최준민"),
    (5, 3, "박지웅", "최준민"),
    (5, 6, "양동일", "황인욱"),
    (5, 6, "양동일", "강민구"),
    (5, 6, "강민구", "김장수"),
    (5, 11, "강민구", "신상준"),
    (5, 11, "김시환", "강민구"),
    (5, 11, "김시환", "이호용"),
    (5, 11, "김시환", "이호용"),
    (5, 12, "강민구", "권재형"),
    (5, 12, "권재형", "황세종"),
    (5, 15, "강민구", "신상준"),
    (5, 15, "이성수", "김민준"),
    (5, 15, "김민준", "이성수"),
    (5, 15, "양동일", "강민구"),
    (5, 15, "양동일", "강민구"),
    (5, 17, "강민구", "권재형"),
    (5, 17, "권재형", "강민구"),
    (5, 17, "강민구", "권재형"),
    (5, 19, "강민구", "김효정"),
    (5, 19, "문국현", "김민준"),
    (5, 19, "김시환", "소강우"),
    (5, 19, "양동일", "강민구"),
    (5, 19, "양동일", "이호용"),
    (5, 20, "이장현", "강민구"),
    (5, 20, "박지웅", "이성수"),
    (5, 20, "김민준", "권재형"),
    (5, 20, "이성수", "김장수"),
    (5, 20, "권재형", "김시환"),
    (5, 20, "문국현", "장혜민"),
    (5, 20, "신상준", "양동일"),
    (5, 21, "강민구", "김장수"),
    (5, 21, "신상준", "김다올"),
    (5, 21, "박지웅", "최준민"),
    (5, 21, "권재형", "김시환"),
    (5, 21, "문국현", "권재형"),
    (5, 21, "문국현", "김시환"),
    (5, 21, "이성수", "이호용"),
    (5, 22, "강민구", "신상준"),
    (5, 22, "강민구", "김효정"),
    (5, 22, "김태세", "김민준"),
    (5, 22, "양동일", "소강우"),
    (5, 22, "김태세", "양동일"),
    (5, 22, "소강우", "김민준"),
]

BOARDS = {
    "notice": {"label": "공지사항", "admin_only": True, "allow_image": False},
    "free": {"label": "자유게시판", "admin_only": False, "allow_image": True},
    "league": {"label": "소셔널 리그", "admin_only": False, "allow_image": True},
    "news": {"label": "소셔널 뉴스", "admin_only": True, "allow_image": True},
    "suggestion": {"label": "건의게시판", "admin_only": False, "allow_image": False},
}

LEAGUE_TYPES = {
    "regular": "정기리그",
    "half": "반기리그",
    "tournament": "토너먼트",
}


def env_value(name, default=""):
    value = os.environ.get(name, "").strip()
    return value if value else default


def db_config():
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        parsed = urlparse(database_url)
        config = {
            "host": parsed.hostname or "db",
            "port": parsed.port or 3306,
            "user": unquote(parsed.username or ""),
            "password": unquote(parsed.password or ""),
            "database": parsed.path.lstrip("/") or env_value("MYSQL_DATABASE", "sotional"),
        }
    else:
        config = {
            "host": env_value("DB_HOST", "db"),
            "port": int(env_value("DB_PORT", "3306")),
            "user": env_value("MYSQL_USER", "sotional_user"),
            "password": env_value("MYSQL_PASSWORD", "sotional_pass"),
            "database": env_value("MYSQL_DATABASE", "sotional"),
        }

    config.update({
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": True,
    })
    ssl_mode = os.environ.get("DB_SSL_MODE", "DISABLED").upper()
    ssl_ca = os.environ.get("DB_SSL_CA", "").strip()
    if ssl_mode in {"REQUIRED", "VERIFY_CA", "VERIFY_IDENTITY"}:
        config["ssl"] = {"ca": ssl_ca} if ssl_ca else {}
    return config


def get_db():
    return pymysql.connect(**db_config())


def wait_for_db():
    for _ in range(60):
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Database is not ready")


def ensure_schema():
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS rating INT NOT NULL DEFAULT 1000",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS sheet_type VARCHAR(40) NULL",
        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS sheet_data LONGTEXT NULL",
        """
        CREATE TABLE IF NOT EXISTS daily_visits (
          visit_date DATE PRIMARY KEY,
          visit_count INT NOT NULL DEFAULT 0,
          updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS system_flags (
          flag_key VARCHAR(120) PRIMARY KEY,
          flag_value VARCHAR(255) NULL,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS schedules (
          id INT AUTO_INCREMENT PRIMARY KEY,
          title VARCHAR(200) NOT NULL,
          event_date DATE NOT NULL,
          start_time TIME NULL,
          location VARCHAR(200) NULL,
          content TEXT NULL,
          created_by INT NOT NULL,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
          CONSTRAINT fk_schedules_author FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
          INDEX idx_schedules_event_date (event_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS rating_matches (
          id INT AUTO_INCREMENT PRIMARY KEY,
          winner_id INT NOT NULL,
          loser_id INT NOT NULL,
          winner_before INT NOT NULL,
          loser_before INT NOT NULL,
          winner_after INT NOT NULL,
          loser_after INT NOT NULL,
          winner_delta INT NOT NULL,
          loser_delta INT NOT NULL,
          memo VARCHAR(255) NULL,
          played_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          recorded_by INT NOT NULL,
          CONSTRAINT fk_rating_winner FOREIGN KEY (winner_id) REFERENCES users(id) ON DELETE CASCADE,
          CONSTRAINT fk_rating_loser FOREIGN KEY (loser_id) REFERENCES users(id) ON DELETE CASCADE,
          CONSTRAINT fk_rating_recorder FOREIGN KEY (recorded_by) REFERENCES users(id) ON DELETE CASCADE,
          INDEX idx_rating_played_at (played_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        "UPDATE users SET rating=1000 WHERE rating IS NULL",
    ]
    with get_db() as conn:
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)


def get_or_create_rating_user(cur, username):
    cur.execute("SELECT id, rating FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    if user:
        return user
    cur.execute(
        "INSERT INTO users (username, password_hash, role, rating) VALUES (%s, %s, 'user', %s)",
        (username, generate_password_hash(uuid4().hex), DEFAULT_RATING),
    )
    cur.execute("SELECT id, rating FROM users WHERE username=%s", (username,))
    return cur.fetchone()


def apply_rating_seed_matches():
    if os.environ.get("ENABLE_RATING_SEED", "").lower() not in {"1", "true", "yes"}:
        return
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT flag_key FROM system_flags WHERE flag_key=%s", (RATING_SEED_FLAG,))
            if cur.fetchone():
                return
            cur.execute("SELECT id FROM users WHERE username='admin'")
            admin_user = cur.fetchone()
            recorder_id = admin_user["id"] if admin_user else 1
            for month, day, winner_name, loser_name in RATING_SEED_MATCHES:
                winner = get_or_create_rating_user(cur, winner_name)
                loser = get_or_create_rating_user(cur, loser_name)
                winner_after, loser_after, winner_delta, loser_delta = calculate_rating(
                    winner["rating"],
                    loser["rating"],
                )
                played_at = f"{RATING_SEED_YEAR}-{month:02d}-{day:02d} 12:00:00"
                cur.execute("UPDATE users SET rating=%s WHERE id=%s", (winner_after, winner["id"]))
                cur.execute("UPDATE users SET rating=%s WHERE id=%s", (loser_after, loser["id"]))
                cur.execute(
                    """
                    INSERT INTO rating_matches (
                      winner_id, loser_id, winner_before, loser_before,
                      winner_after, loser_after, winner_delta, loser_delta, memo, played_at, recorded_by
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        winner["id"],
                        loser["id"],
                        winner["rating"],
                        loser["rating"],
                        winner_after,
                        loser_after,
                        winner_delta,
                        loser_delta,
                        "레이팅 대국",
                        played_at,
                        recorder_id,
                    ),
                )
            cur.execute(
                "INSERT INTO system_flags (flag_key, flag_value) VALUES (%s, %s)",
                (RATING_SEED_FLAG, str(len(RATING_SEED_MATCHES))),
            )


def ensure_admin():
    with get_db() as conn:
        with conn.cursor() as cur:
            admin_username = env_value("ADMIN_USERNAME", "admin")
            admin_password = env_value("ADMIN_PASSWORD", "admin")
            cur.execute("SELECT id FROM users WHERE username=%s", (admin_username,))
            user = cur.fetchone()
            password_hash = generate_password_hash(admin_password)
            if user and os.environ.get("FORCE_RESET_ADMIN", "").lower() in {"1", "true", "yes"}:
                cur.execute(
                    "UPDATE users SET password_hash=%s, role='admin' WHERE username=%s",
                    (password_hash, admin_username),
                )
            elif not user:
                cur.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'admin')",
                    (admin_username, password_hash),
                )


@app.before_request
def count_daily_visit():
    if request.endpoint in {"static"}:
        return
    today_key = date.today().isoformat()
    session_key = f"visited_{today_key}"
    if session.get(session_key):
        return
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO daily_visits (visit_date, visit_count)
                    VALUES (CURDATE(), 1)
                    ON DUPLICATE KEY UPDATE visit_count = visit_count + 1
                    """
                )
        session[session_key] = True
    except Exception:
        pass


def current_user():
    if "user_id" not in session:
        return None
    return {
        "id": session["user_id"],
        "username": session["username"],
        "role": session["role"],
        "is_admin": session["role"] == "admin",
        "rating": session.get("rating", DEFAULT_RATING),
    }


@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "boards": BOARDS,
        "league_types": LEAGUE_TYPES,
        "sheet_types": SHEET_TYPES,
        "tournament_sizes": TOURNAMENT_SIZES,
        "can_manage_post": can_manage_post,
        "image_url": image_url,
    }


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("로그인이 필요합니다.")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user or not user["is_admin"]:
            flash("관리자 권한이 필요합니다.")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)

    return wrapper


def can_write(board):
    user = current_user()
    if not user:
        return False
    if board not in BOARDS:
        return False
    return user["is_admin"] or not BOARDS[board]["admin_only"]


def can_manage_post(post):
    user = current_user()
    return bool(user and (user["is_admin"] or user["id"] == post["author_id"]))


def calculate_rating(winner_rating, loser_rating):
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    winner_delta = max(1, round(RATING_K_FACTOR * (1 - expected_winner)))
    loser_delta = -winner_delta
    return winner_rating + winner_delta, loser_rating + loser_delta, winner_delta, loser_delta


def calculate_league_rankings(rows):
    players = []
    for row in rows:
        if len(row) < 2:
            continue
        name = row[1]
        wins = 0
        for cell in row[2:]:
            normalized = str(cell).strip().lower()
            if normalized in {"승", "win", "w", "1", "o", "○"}:
                wins += 1
        players.append({"name": name, "wins": wins})
    sorted_players = sorted(players, key=lambda item: (-item["wins"], item["name"]))
    rank_by_name = {}
    previous_wins = None
    current_rank = 0
    for index, player in enumerate(sorted_players, start=1):
        if previous_wins is None or player["wins"] != previous_wins:
            current_rank = index
        rank_by_name[player["name"]] = current_rank
        previous_wins = player["wins"]
    return [{"rank": rank_by_name.get(player["name"], ""), **player} for player in players]


def apply_league_ranks(sheet):
    rows = sheet.get("rows", [])
    rankings = calculate_league_rankings(rows)
    rank_by_name = {item["name"]: item["rank"] for item in rankings}
    for row in rows:
        if len(row) >= 2:
            row[0] = str(rank_by_name.get(row[1], ""))
    sheet["rankings"] = sorted(rankings, key=lambda item: (item["rank"] or 999, -item["wins"], item["name"]))
    return sheet


def next_power_of_two(value):
    size = 1
    while size < value:
        size *= 2
    return size


def build_tournament_rounds(names, bracket_size):
    bracket_size = int(bracket_size)
    padded = names[:bracket_size] + [""] * max(0, bracket_size - len(names))
    rounds = []
    current_count = bracket_size
    first_round = []
    for index in range(0, bracket_size, 2):
        player_a = padded[index] or "부전승"
        player_b = padded[index + 1] or "부전승"
        first_round.append({"player1": player_a, "player2": player_b, "winner": ""})
    rounds.append(first_round)
    current_count //= 2
    while current_count >= 1:
        rounds.append([{"player1": "", "player2": "", "winner": ""} for _ in range(current_count // 2 or 1)])
        current_count //= 2
        if len(rounds[-1]) == 1:
            break
    return rounds


def advance_tournament(rounds):
    for round_index in range(len(rounds) - 1):
        winners = [match.get("winner", "").strip() for match in rounds[round_index]]
        next_round = rounds[round_index + 1]
        for match_index, match in enumerate(next_round):
            match["player1"] = winners[match_index * 2] if match_index * 2 < len(winners) else ""
            match["player2"] = winners[match_index * 2 + 1] if match_index * 2 + 1 < len(winners) else ""
            if match.get("winner") not in {match["player1"], match["player2"]}:
                match["winner"] = ""
    return rounds


def tournament_results(rounds):
    if not rounds or not rounds[-1]:
        return []
    final_match = rounds[-1][0]
    champion = final_match.get("winner", "").strip()
    if not champion:
        return []
    finalists = [final_match.get("player1", "").strip(), final_match.get("player2", "").strip()]
    runner_up = next((name for name in finalists if name and name != champion), "")
    semi_losers = []
    if len(rounds) >= 2:
        for match in rounds[-2]:
            players = [match.get("player1", "").strip(), match.get("player2", "").strip()]
            winner = match.get("winner", "").strip()
            for player in players:
                if player and player != winner and player != "부전승":
                    semi_losers.append(player)
    results = [("우승", champion)]
    if runner_up:
        results.append(("준우승", runner_up))
    if semi_losers:
        results.append(("3위", semi_losers[0]))
    if len(semi_losers) > 1:
        results.append(("4위", semi_losers[1]))
    return results


def build_sheet(sheet_type, participants, bracket_size=None):
    names = [name for name in participants if name]
    if not sheet_type or sheet_type not in SHEET_TYPES or not names:
        return None
    if sheet_type == "league":
        rows = [["순위", "참가자"] + names]
        for name in names:
            rows.append(["", name] + ["-" if name == opponent else "" for opponent in names])
        return apply_league_ranks({"mode": "table", "title": "리그전 대진표", "headers": rows[0], "rows": rows[1:]})
    if sheet_type == "tournament":
        size = int(bracket_size or next_power_of_two(len(names)))
        if size not in {4, 8, 16}:
            size = 8
        rounds = build_tournament_rounds(names, size)
        return {
            "mode": "bracket",
            "title": f"{size}강 토너먼트 대진표",
            "bracket_size": size,
            "rounds": advance_tournament(rounds),
            "results": [],
        }
    if sheet_type == "team":
        rows = [[str(index + 1), name, "", "", ""] for index, name in enumerate(names)]
        return {"mode": "table", "title": "팀전 명단표", "headers": ["순번", "참가자", "소속팀", "상대", "결과"], "rows": rows}
    rows = [[str(index + 1), name, "", "", ""] for index, name in enumerate(names)]
    return {"mode": "table", "title": "대항전 오더표", "headers": ["오더", "우리팀", "상대팀", "결과", "비고"], "rows": rows}


def parse_sheet_data(raw_data):
    if not raw_data:
        return None
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    data.setdefault("mode", "table")
    data.setdefault("headers", [])
    data.setdefault("rows", [])
    if data.get("mode") == "bracket":
        data.setdefault("rounds", [])
        data["results"] = tournament_results(data["rounds"])
    return data


@app.template_filter("time_input")
def time_input(value):
    if not value:
        return ""
    text = str(value)
    parts = text.split(":")
    if len(parts) >= 2:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    return text


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def image_url(path):
    if not path:
        return ""
    if path.startswith(("http://", "https://")):
        return path
    return url_for("static", filename=path)


def upload_to_object_storage(file, filename):
    try:
        import boto3
    except ImportError:
        flash("외부 이미지 저장소 패키지가 설치되지 않았습니다.")
        return None

    bucket = env_value("S3_BUCKET")
    endpoint_url = env_value("S3_ENDPOINT_URL")
    public_base_url = env_value("S3_PUBLIC_BASE_URL")
    access_key = env_value("S3_ACCESS_KEY_ID")
    secret_key = env_value("S3_SECRET_ACCESS_KEY")
    region = env_value("S3_REGION", "auto")
    if not all([bucket, endpoint_url, public_base_url, access_key, secret_key]):
        flash("외부 이미지 저장소 환경변수가 부족합니다.")
        return None

    key = f"uploads/{filename}"
    content_type = file.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    file.stream.seek(0)
    client.upload_fileobj(
        file.stream,
        bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{public_base_url.rstrip('/')}/{key}"


def save_upload(file):
    if not file or file.filename == "":
        return None
    if not allowed_file(file.filename):
        flash("이미지는 png, jpg, jpeg, gif, webp 형식만 업로드할 수 있습니다.")
        return None
    safe_name = secure_filename(file.filename)
    filename = f"{uuid4().hex}_{safe_name}"
    if env_value("STORAGE_BACKEND", "local").lower() in {"s3", "r2"}:
        return upload_to_object_storage(file, filename)
    file.save(UPLOAD_FOLDER / filename)
    return f"uploads/{filename}"


def get_post(post_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.*, u.username
                FROM posts p
                JOIN users u ON u.id = p.author_id
                WHERE p.id=%s
                """,
                (post_id,),
            )
            post = cur.fetchone()
    if post:
        post["sheet"] = parse_sheet_data(post.get("sheet_data"))
    return post


def get_month_context(year_value=None, month_value=None):
    today = date.today()
    year_value = year_value or today.year
    month_value = month_value or today.month
    if month_value < 1:
        year_value -= 1
        month_value = 12
    if month_value > 12:
        year_value += 1
        month_value = 1
    first_day = date(year_value, month_value, 1)
    if month_value == 12:
        next_month = date(year_value + 1, 1, 1)
    else:
        next_month = date(year_value, month_value + 1, 1)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.*, u.username
                FROM schedules s
                JOIN users u ON u.id = s.created_by
                WHERE s.event_date >= %s AND s.event_date < %s
                ORDER BY s.event_date, s.start_time, s.id
                """,
                (first_day, next_month),
            )
            schedules = cur.fetchall()
    schedules_by_day = {}
    for item in schedules:
        schedules_by_day.setdefault(item["event_date"].day, []).append(item)
    weeks = []
    for week in Calendar(firstweekday=6).monthdatescalendar(year_value, month_value):
        weeks.append(
            [
                {
                    "date": day,
                    "in_month": day.month == month_value,
                    "schedules": schedules_by_day.get(day.day, []) if day.month == month_value else [],
                }
                for day in week
            ]
        )
    prev_month = month_value - 1
    prev_year = year_value
    next_month_num = month_value + 1
    next_year = year_value
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    if next_month_num > 12:
        next_month_num = 1
        next_year += 1
    return {
        "year": year_value,
        "month": month_value,
        "month_name": month_name[month_value],
        "weeks": weeks,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month_num,
    }


@app.route("/")
def index():
    if not current_user():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT s.*
                FROM schedules s
                WHERE s.event_date >= CURDATE()
                ORDER BY s.event_date, s.start_time
                LIMIT 5
                """
            )
            upcoming = cur.fetchall()
            cur.execute("SELECT username, rating FROM users ORDER BY rating DESC, username LIMIT 5")
            leaders = cur.fetchall()
            cur.execute("SELECT visit_count FROM daily_visits WHERE visit_date = CURDATE()")
            visit_row = cur.fetchone()
    today_visits = visit_row["visit_count"] if visit_row else 0
    return render_template("dashboard.html", upcoming=upcoming, leaders=leaders, today_visits=today_visits)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username=%s", (username,))
                user = cur.fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["rating"] = user.get("rating", DEFAULT_RATING)
            return redirect(url_for("index"))
        flash("아이디 또는 비밀번호가 올바르지 않습니다.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/account/password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not current_password or not new_password or not confirm_password:
            flash("현재 비밀번호와 새 비밀번호를 모두 입력하세요.")
        elif new_password != confirm_password:
            flash("새 비밀번호 확인이 일치하지 않습니다.")
        elif len(new_password) < 4:
            flash("새 비밀번호는 4자 이상으로 입력하세요.")
        else:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT password_hash FROM users WHERE id=%s", (session["user_id"],))
                    user = cur.fetchone()
                    if not user or not check_password_hash(user["password_hash"], current_password):
                        flash("현재 비밀번호가 올바르지 않습니다.")
                    else:
                        cur.execute(
                            "UPDATE users SET password_hash=%s WHERE id=%s",
                            (generate_password_hash(new_password), session["user_id"]),
                        )
                        flash("비밀번호를 변경했습니다.")
                        return redirect(url_for("dashboard"))
    return render_template("change_password.html")


@app.route("/admin/users", methods=["GET", "POST"])
@admin_required
def users():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")
        if not username or not password:
            flash("아이디와 비밀번호를 입력하세요.")
        elif role not in {"admin", "user"}:
            flash("권한 값이 올바르지 않습니다.")
        else:
            try:
                with get_db() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                            (username, generate_password_hash(password), role),
                        )
                flash("계정을 생성했습니다.")
            except pymysql.err.IntegrityError:
                flash("이미 존재하는 아이디입니다.")
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, role, rating, created_at FROM users ORDER BY id")
            rows = cur.fetchall()
    return render_template("users.html", users=rows)


@app.route("/board/<board>")
@login_required
def board(board):
    if board not in BOARDS:
        return redirect(url_for("index"))
    league_type = request.args.get("league_type")
    keyword = request.args.get("q", "").strip()
    params = [board]
    query = """
        SELECT p.*, u.username
        FROM posts p
        JOIN users u ON u.id = p.author_id
        WHERE p.board=%s
    """
    if board == "league":
        if league_type not in LEAGUE_TYPES:
            league_type = "regular"
        query += " AND p.league_type=%s"
        params.append(league_type)
    else:
        league_type = None
    if keyword:
        query += " AND (p.title LIKE %s OR p.content LIKE %s OR u.username LIKE %s)"
        like_keyword = f"%{keyword}%"
        params.extend([like_keyword, like_keyword, like_keyword])
    query += " ORDER BY p.created_at DESC"
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            posts = cur.fetchall()
    return render_template(
        "board.html",
        board=board,
        league_type=league_type,
        posts=posts,
        can_write=can_write(board),
        keyword=keyword,
    )


@app.route("/board/<board>/new", methods=["GET", "POST"])
@login_required
def new_post(board):
    if board not in BOARDS:
        return redirect(url_for("index"))
    if not can_write(board):
        flash("이 게시판에는 관리자만 글을 작성할 수 있습니다.")
        return redirect(url_for("board", board=board))
    league_type = request.args.get("league_type") if board == "league" else None
    if board == "league" and league_type not in LEAGUE_TYPES:
        league_type = "regular"
    users = []
    if board == "league":
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, username, rating FROM users ORDER BY username")
                users = cur.fetchall()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        image_path = save_upload(request.files.get("image")) if BOARDS[board]["allow_image"] else None
        sheet_type = request.form.get("sheet_type") if board == "league" else None
        bracket_size = request.form.get("bracket_size") if board == "league" else None
        participant_names = request.form.getlist("participants")
        sheet = build_sheet(sheet_type, participant_names, bracket_size)
        sheet_data = json.dumps(sheet, ensure_ascii=False) if sheet else None
        sheet_type = sheet_type if sheet else None
        if not title or not content:
            flash("제목과 내용을 입력하세요.")
        else:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO posts (board, league_type, title, content, image_path, sheet_type, sheet_data, author_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (board, league_type, title, content, image_path, sheet_type, sheet_data, session["user_id"]),
                    )
            return redirect(url_for("board", board=board, league_type=league_type))
    return render_template("post_form.html", board=board, league_type=league_type, users=users)


@app.route("/post/<int:post_id>")
@login_required
def post_detail(post_id):
    post = get_post(post_id)
    if not post:
        flash("글을 찾을 수 없습니다.")
        return redirect(url_for("index"))
    return render_template("post_detail.html", post=post)


@app.route("/post/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = get_post(post_id)
    if not post:
        flash("글을 찾을 수 없습니다.")
        return redirect(url_for("index"))
    if not can_manage_post(post):
        flash("작성자 또는 관리자만 수정할 수 있습니다.")
        return redirect(url_for("post_detail", post_id=post_id))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        image_path = post["image_path"]
        if BOARDS[post["board"]]["allow_image"]:
            uploaded = save_upload(request.files.get("image"))
            image_path = uploaded or image_path
        if not title or not content:
            flash("제목과 내용을 입력하세요.")
        else:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE posts
                        SET title=%s, content=%s, image_path=%s
                        WHERE id=%s
                        """,
                        (title, content, image_path, post_id),
                    )
            flash("글을 수정했습니다.")
            return redirect(url_for("post_detail", post_id=post_id))
    return render_template("post_form.html", board=post["board"], league_type=post["league_type"], post=post)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = get_post(post_id)
    if not post:
        flash("글을 찾을 수 없습니다.")
        return redirect(url_for("index"))
    if not can_manage_post(post):
        flash("작성자 또는 관리자만 삭제할 수 있습니다.")
        return redirect(url_for("post_detail", post_id=post_id))
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM posts WHERE id=%s", (post_id,))
    flash("글을 삭제했습니다.")
    return redirect(url_for("board", board=post["board"], league_type=post["league_type"]))


@app.route("/post/<int:post_id>/sheet", methods=["POST"])
@login_required
def update_sheet(post_id):
    post = get_post(post_id)
    if not post or post["board"] != "league" or not post.get("sheet"):
        flash("수정할 리그표를 찾을 수 없습니다.")
        return redirect(url_for("index"))
    if post["sheet"].get("mode") == "bracket":
        round_count = request.form.get("round_count", type=int) or 0
        rounds = []
        for round_index in range(round_count):
            match_count = request.form.get(f"match_count_{round_index}", type=int) or 0
            matches = []
            for match_index in range(match_count):
                prefix = f"round_{round_index}_match_{match_index}"
                matches.append(
                    {
                        "player1": request.form.get(f"{prefix}_player1", "").strip(),
                        "player2": request.form.get(f"{prefix}_player2", "").strip(),
                        "winner": request.form.get(f"{prefix}_winner", "").strip(),
                    }
                )
            rounds.append(matches)
        sheet = {
            "mode": "bracket",
            "title": post["sheet"].get("title", SHEET_TYPES.get(post.get("sheet_type"), "토너먼트")),
            "bracket_size": post["sheet"].get("bracket_size"),
            "rounds": advance_tournament(rounds),
        }
        sheet["results"] = tournament_results(sheet["rounds"])
    else:
        headers = request.form.getlist("headers")
        row_count = request.form.get("row_count", type=int) or 0
        rows = []
        for row_index in range(row_count):
            row = request.form.getlist(f"row_{row_index}")
            if row:
                rows.append(row)
        sheet = {
            "mode": "table",
            "title": post["sheet"].get("title", SHEET_TYPES.get(post.get("sheet_type"), "리그표")),
            "headers": headers,
            "rows": rows,
        }
        if post.get("sheet_type") == "league":
            sheet = apply_league_ranks(sheet)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE posts SET sheet_data=%s WHERE id=%s",
                (json.dumps(sheet, ensure_ascii=False), post_id),
            )
    flash("리그표를 저장했습니다.")
    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/schedule")
@login_required
def schedule():
    today = date.today()
    year_value = request.args.get("year", today.year, type=int)
    month_value = request.args.get("month", today.month, type=int)
    context = get_month_context(year_value, month_value)
    return render_template("schedule.html", **context)


@app.route("/schedule/new", methods=["GET", "POST"])
@admin_required
def new_schedule():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        event_date = request.form.get("event_date", "").strip()
        start_time = request.form.get("start_time", "").strip() or None
        location = request.form.get("location", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not event_date:
            flash("일정 제목과 날짜를 입력하세요.")
        else:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO schedules (title, event_date, start_time, location, content, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (title, event_date, start_time, location, content, session["user_id"]),
                    )
            flash("일정을 추가했습니다.")
            selected = datetime.strptime(event_date, "%Y-%m-%d").date()
            return redirect(url_for("schedule", year=selected.year, month=selected.month))
    return render_template("schedule_form.html", item=None)


@app.route("/schedule/<int:schedule_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_schedule(schedule_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM schedules WHERE id=%s", (schedule_id,))
            item = cur.fetchone()
    if not item:
        flash("일정을 찾을 수 없습니다.")
        return redirect(url_for("schedule"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        event_date = request.form.get("event_date", "").strip()
        start_time = request.form.get("start_time", "").strip() or None
        location = request.form.get("location", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not event_date:
            flash("일정 제목과 날짜를 입력하세요.")
        else:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE schedules
                        SET title=%s, event_date=%s, start_time=%s, location=%s, content=%s
                        WHERE id=%s
                        """,
                        (title, event_date, start_time, location, content, schedule_id),
                    )
            flash("일정을 수정했습니다.")
            selected = datetime.strptime(event_date, "%Y-%m-%d").date()
            return redirect(url_for("schedule", year=selected.year, month=selected.month))
    return render_template("schedule_form.html", item=item)


@app.route("/schedule/<int:schedule_id>/delete", methods=["POST"])
@admin_required
def delete_schedule(schedule_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT event_date FROM schedules WHERE id=%s", (schedule_id,))
            item = cur.fetchone()
            cur.execute("DELETE FROM schedules WHERE id=%s", (schedule_id,))
    flash("일정을 삭제했습니다.")
    if item:
        return redirect(url_for("schedule", year=item["event_date"].year, month=item["event_date"].month))
    return redirect(url_for("schedule"))


@app.route("/rating", methods=["GET", "POST"])
@login_required
def rating():
    if request.method == "POST":
        user = current_user()
        if not user["is_admin"]:
            flash("관리자만 대국 결과를 등록할 수 있습니다.")
            return redirect(url_for("rating"))
        winner_id = request.form.get("winner_id", type=int)
        loser_id = request.form.get("loser_id", type=int)
        memo = request.form.get("memo", "").strip()
        if not winner_id or not loser_id or winner_id == loser_id:
            flash("승자와 패자를 올바르게 선택하세요.")
        else:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, rating FROM users WHERE id IN (%s, %s)", (winner_id, loser_id))
                    selected = {row["id"]: row for row in cur.fetchall()}
                    if winner_id not in selected or loser_id not in selected:
                        flash("선택한 계정을 찾을 수 없습니다.")
                    else:
                        winner_before = selected[winner_id]["rating"]
                        loser_before = selected[loser_id]["rating"]
                        winner_after, loser_after, winner_delta, loser_delta = calculate_rating(
                            winner_before,
                            loser_before,
                        )
                        cur.execute("UPDATE users SET rating=%s WHERE id=%s", (winner_after, winner_id))
                        cur.execute("UPDATE users SET rating=%s WHERE id=%s", (loser_after, loser_id))
                        cur.execute(
                            """
                            INSERT INTO rating_matches (
                              winner_id, loser_id, winner_before, loser_before,
                              winner_after, loser_after, winner_delta, loser_delta, memo, recorded_by
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                winner_id,
                                loser_id,
                                winner_before,
                                loser_before,
                                winner_after,
                                loser_after,
                                winner_delta,
                                loser_delta,
                                memo,
                                session["user_id"],
                            ),
                        )
                        if session["user_id"] in {winner_id, loser_id}:
                            session["rating"] = winner_after if session["user_id"] == winner_id else loser_after
                        flash(f"레이팅을 반영했습니다. 승자 {winner_delta:+d}점, 패자 {loser_delta:+d}점")
        return redirect(url_for("rating"))
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, rating FROM users ORDER BY rating DESC, username")
            users = cur.fetchall()
            cur.execute(
                """
                SELECT rm.*, w.username AS winner_name, l.username AS loser_name, r.username AS recorder_name
                FROM rating_matches rm
                JOIN users w ON w.id = rm.winner_id
                JOIN users l ON l.id = rm.loser_id
                JOIN users r ON r.id = rm.recorded_by
                ORDER BY rm.played_at ASC, rm.id ASC
                LIMIT 300
                """
            )
            matches = cur.fetchall()
    return render_template("rating.html", users=users, matches=matches)


@app.route("/rating/user/<int:user_id>")
@login_required
def rating_user(user_id):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username, rating FROM users WHERE id=%s", (user_id,))
            target = cur.fetchone()
            if not target:
                flash("사용자를 찾을 수 없습니다.")
                return redirect(url_for("rating"))
            cur.execute("SELECT COUNT(*) AS wins FROM rating_matches WHERE winner_id=%s", (user_id,))
            wins = cur.fetchone()["wins"]
            cur.execute("SELECT COUNT(*) AS losses FROM rating_matches WHERE loser_id=%s", (user_id,))
            losses = cur.fetchone()["losses"]
            cur.execute(
                """
                SELECT
                  rm.*,
                  w.username AS winner_name,
                  l.username AS loser_name,
                  CASE WHEN rm.winner_id = %s THEN 'win' ELSE 'loss' END AS result,
                  CASE WHEN rm.winner_id = %s THEN l.username ELSE w.username END AS opponent_name,
                  CASE WHEN rm.winner_id = %s THEN rm.winner_delta ELSE rm.loser_delta END AS rating_delta,
                  CASE WHEN rm.winner_id = %s THEN rm.winner_after ELSE rm.loser_after END AS rating_after
                FROM rating_matches rm
                JOIN users w ON w.id = rm.winner_id
                JOIN users l ON l.id = rm.loser_id
                WHERE rm.winner_id=%s OR rm.loser_id=%s
                ORDER BY rm.played_at DESC, rm.id DESC
                """,
                (user_id, user_id, user_id, user_id, user_id, user_id),
            )
            history = cur.fetchall()
    return render_template(
        "rating_user.html",
        target=target,
        wins=wins,
        losses=losses,
        history=history,
    )


if __name__ == "__main__":
    wait_for_db()
    ensure_schema()
    ensure_admin()
    apply_rating_seed_matches()
    app.run(host="0.0.0.0", port=int(env_value("PORT", "5000")))
