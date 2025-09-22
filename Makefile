# Project: braintransplant-ai — File: Makefile
# Minimal Makefile for braintransplant-ai (Postgres + Web UI)

# ======== Constants (no defaults) ========
DB_USER       = braintransplant_ai_user
DB_NAME       = braintransplant_ai_db

# ======== Public targets ========

# Basic redeploy: rebuild app (keeps DB volume & outputs) and start services.
redeploy:
	docker compose build app
	$(MAKE) _start

# Clean redeploy: reset DB schema to empty (drop/recreate public), re-apply schema, then start.
redeploy-clean:
	$(MAKE) _db-reset-schema
	$(MAKE) _start

# Hard redeploy: remove containers & volumes, prune Docker cache, then start fresh.
redeploy-hard:
	$(MAKE) _hard-reset
	$(MAKE) _start

# psql shell into the running DB.
psql:
	docker compose exec db psql -U $(DB_USER) -d $(DB_NAME)

# Show estimated row counts for user tables.
show-db-stats:
	docker compose exec db psql -U $(DB_USER) -d $(DB_NAME) -c "\
		SELECT relname AS table, n_live_tup AS estimated_rows \
		FROM pg_stat_user_tables \
		ORDER BY relname;"

# ======== Internal helpers (underscored) ========

# Start DB then app and print URLs.
_start:
	@echo "Starting Postgres and app..."
	docker compose up -d db
	docker compose up -d app
	@echo ""
	@echo "Chat/UI: http://localhost:8502/"

# Remove containers + named volumes and global unused data, then bring DB up (app started by _start).
_hard-reset:
	docker compose down -v || true
	docker system prune -af --volumes || true
	docker compose up -d db

# Reset DB to an empty state by dropping and recreating the public schema, then re-apply schema.sql via app.
_db-reset-schema:
	docker compose exec db psql -U $(DB_USER) -d $(DB_NAME) -v ON_ERROR_STOP=1 -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO $(DB_USER);"
	$(MAKE) _db-apply-schema

# Apply db/schema.sql via the app container (uses db.init_db module).
_db-apply-schema:
	docker compose run --rm app python -m db.init_db

.PHONY: redeploy redeploy-clean redeploy-hard psql show-db-stats _start _hard-reset _db-reset-schema _db-apply-schema
