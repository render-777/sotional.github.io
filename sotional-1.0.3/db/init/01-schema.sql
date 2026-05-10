CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
  rating INT NOT NULL DEFAULT 1000,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS posts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  board VARCHAR(40) NOT NULL,
  league_type VARCHAR(40) NULL,
  title VARCHAR(200) NOT NULL,
  content TEXT NOT NULL,
  image_path VARCHAR(255) NULL,
  author_id INT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_posts_author FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_posts_board (board),
  INDEX idx_posts_league_type (league_type),
  INDEX idx_posts_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
