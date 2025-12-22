-- Створення користувача для реплікації
-- Використовуємо змінну оточення для назви БД
DO $$
DECLARE
    db_name text := current_database();
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'repuser') THEN
        CREATE USER repuser WITH REPLICATION PASSWORD 'repuser';
    END IF;
    
    -- Надання необхідних прав
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO repuser', db_name);
    GRANT USAGE ON SCHEMA public TO repuser;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO repuser;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO repuser;
END
$$;
