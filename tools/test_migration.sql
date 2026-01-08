CREATE TABLE IF NOT EXISTS maintenance_log (
    id SERIAL PRIMARY KEY,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message TEXT
);
INSERT INTO maintenance_log (message) VALUES ('Migration executed by shard_executor');

