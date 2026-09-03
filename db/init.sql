-- Runs once on first container start (empty data volume).
-- The database itself is created by the MARIADB_DATABASE env var; here we just
-- pin the charset. All tables are created by SQLAlchemy (init_schema()).
ALTER DATABASE fintomy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
