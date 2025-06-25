DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'atomia_user') THEN
      CREATE ROLE atomia_user LOGIN PASSWORD 'atomia_password';
   END IF;
END$$;

CREATE DATABASE atomia_dev OWNER atomia_user; 