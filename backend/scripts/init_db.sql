-- AI-Driven Scheme Discovery — PostgreSQL initialization script
-- Runs once on fresh container start (docker-entrypoint-initdb.d)
-- Full schema is managed by Alembic migrations — this only enables extensions.

-- Enable pgvector for semantic similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search dictionaries (for future tsvector columns)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
