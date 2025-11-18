-- PostgreSQL Database Initialization Script
-- Run as a superuser (e.g., postgres)
-- Note: Replace <password> with a strong password.

-- ============================================
-- Step 1: Create database
-- ============================================
CREATE DATABASE cstrader
  WITH ENCODING 'UTF8'
       LC_COLLATE 'C'
       LC_CTYPE 'C'
       TEMPLATE template0;

-- ============================================
-- Step 2: Create role/user (optional)
-- ============================================
CREATE ROLE cstrader_user WITH LOGIN PASSWORD '2Ts9zM2%';
ALTER ROLE cstrader_user SET search_path = public;

-- ============================================
-- Step 3: Grant access (optional)
-- ============================================
GRANT ALL PRIVILEGES ON DATABASE cstrader TO cstrader_user;

-- Grant permissions on public schema
GRANT ALL PRIVILEGES ON SCHEMA public TO cstrader_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cstrader_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cstrader_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO cstrader_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cstrader_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cstrader_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO cstrader_user;

-- ============================================
-- Connection string
-- ============================================
-- psql "host=localhost port=5432 user=cstrader_user dbname=cstrader"
