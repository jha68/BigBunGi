CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, expires INTEGER NOT NULL, auth_version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS login_attempts (ip TEXT PRIMARY KEY, failures INTEGER NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS practice (id TEXT PRIMARY KEY, revision INTEGER NOT NULL DEFAULT 0, data TEXT, updated_at TEXT);
INSERT OR IGNORE INTO practice (id, revision) VALUES ('owner', 0);
CREATE TABLE IF NOT EXISTS gemini_settings (id TEXT PRIMARY KEY, revision INTEGER NOT NULL DEFAULT 0, data TEXT, updated_at TEXT);
INSERT OR IGNORE INTO gemini_settings (id, revision) VALUES ('owner', 0);
