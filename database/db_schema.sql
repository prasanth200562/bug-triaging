-- Bug Triaging System Database Schema (SQLite)

-- Users table for RBAC
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT CHECK(role IN ('admin', 'developer', 'reporter')) DEFAULT 'reporter',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bugs table to store reported issues
CREATE TABLE IF NOT EXISTS bugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
    tags TEXT, -- Comma-separated or JSON string
    source TEXT CHECK(source IN ('manual', 'github')) DEFAULT 'manual',
    status TEXT CHECK(status IN ('open', 'in-progress', 'manual-review', 'assigned', 'closed')) DEFAULT 'open',
    reporter_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reporter_id) REFERENCES users(id)
);

-- Store ML prediction results for each bug
CREATE TABLE IF NOT EXISTS model_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bug_id INTEGER NOT NULL,
    predicted_developer TEXT NOT NULL,
    confidence REAL NOT NULL,
    top_alternatives TEXT, -- JSON string of top K predictions
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    threshold_used REAL DEFAULT 0.50,
    FOREIGN KEY (bug_id) REFERENCES bugs(id)
);

-- Track final assignments and transitions
CREATE TABLE IF NOT EXISTS bug_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bug_id INTEGER NOT NULL,
    developer_id INTEGER,
    developer_name TEXT, -- Fallback for when developer user doesn't exist yet
    assigned_by_id INTEGER, -- Admin who assigned it
    assignment_type TEXT CHECK(assignment_type IN ('auto', 'manual')) NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bug_id) REFERENCES bugs(id),
    FOREIGN KEY (developer_id) REFERENCES users(id),
    FOREIGN KEY (assigned_by_id) REFERENCES users(id)
);

-- Log manual reviews and overrides for retraining
CREATE TABLE IF NOT EXISTS manual_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bug_id INTEGER NOT NULL,
    prediction_id INTEGER,
    reviewer_id INTEGER NOT NULL,
    original_prediction TEXT,
    corrected_developer TEXT,
    review_notes TEXT,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bug_id) REFERENCES bugs(id),
    FOREIGN KEY (prediction_id) REFERENCES model_predictions(id),
    FOREIGN KEY (reviewer_id) REFERENCES users(id)
);

-- For GitHub sync tracking
CREATE TABLE IF NOT EXISTS github_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bug_id INTEGER UNIQUE NOT NULL,
    github_id INTEGER UNIQUE NOT NULL,
    issue_number INTEGER NOT NULL,
    repo_full_name TEXT NOT NULL,
    last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bug_id) REFERENCES bugs(id)
);

-- Training data accumulation
CREATE TABLE IF NOT EXISTS training_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bug_id INTEGER UNIQUE NOT NULL,
    title TEXT,
    body TEXT,
    assigned_developer TEXT,
    is_verified_label BOOLEAN DEFAULT 0,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bug_id) REFERENCES bugs(id)
);

-- Seed some developers for testing
INSERT OR IGNORE INTO users (username, password_hash, full_name, role) VALUES 
('admin', 'pbkdf2:sha256:260000$xxxx', 'System Admin', 'admin'),
('dev1', 'pbkdf2:sha256:260000$xxxx', 'Alice Smith', 'developer'),
('dev2', 'pbkdf2:sha256:260000$xxxx', 'Bob Johnson', 'developer'),
('dev3', 'pbkdf2:sha256:260000$xxxx', 'Charlie Brown', 'developer');
