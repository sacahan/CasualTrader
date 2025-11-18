-- Run as a superuser (e.g., postgres) on sacahan-ubunto:5432
-- 1) Create role/user (optional but recommended)
-- NOTE: Replace <password> with a strong password.
-- CREATE ROLE cstrader_user WITH LOGIN PASSWORD '<password>';
-- ALTER ROLE cstrader_user SET search_path = public;

-- 2) Create database (ignore error if it already exists)
DO $$ BEGIN
   IF NOT EXISTS (
     SELECT FROM pg_database WHERE datname = 'cstrader'
   ) THEN
     PERFORM dblink_exec('dbname=' || current_database(), $$CREATE DATABASE cstrader
       WITH ENCODING 'UTF8'
            LC_COLLATE 'C'
            LC_CTYPE 'C'
            TEMPLATE template0$$);
   END IF;
EXCEPTION WHEN undefined_function THEN
   -- dblink may not be available; fallback
   RAISE NOTICE 'Please run: CREATE DATABASE cstrader WITH TEMPLATE template0 ENCODING ''UTF8'';';
END $$;

-- 3) Grant access
-- GRANT ALL PRIVILEGES ON DATABASE cstrader TO cstrader_user;

-- Connect:
-- psql "host=sacahan-ubunto port=5432 user=cstrader_user dbname=cstrader password=<password>"
