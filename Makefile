# Project: braintransplant-ai — File: Makefile
# Minimal Makefile for braintransplant-ai (Postgres + Web UI)

# ======== Constants (no defaults) ========
DB_USER      = braintransplant_ai_user
DB_NAME      = braintransplant_ai_db
LOG_DIR_HOST = outputs/logs
LOG_DIR_APP  = /app/outputs/logs

# ======== Public targets ========

# Basic redeploy: clear logs, rebuild app (keeps DB volume), start services.
redeploy:
	$(MAKE) clean-logs
	docker compose build app
	$(MAKE) _start

# Clean redeploy: reset DB schema to empty (drop/recreate public), re-apply schema, then start.
redeploy-clean:
	$(MAKE) clean-logs
	$(MAKE) _db-reset-schema
	$(MAKE) _start

# Hard redeploy: remove containers & volumes, prune Docker cache, then start fresh.
redeploy-hard:
	$(MAKE) clean-logs
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

# Truncate app logs (host + running container, if present) to empty them.
clean-logs:
	@echo "Emptying host logs in $(LOG_DIR_HOST)…"
	mkdir -p "$(LOG_DIR_HOST)"
	@# Truncate log files to zero bytes without deleting them
	-find "$(LOG_DIR_HOST)" -maxdepth 1 -type f -name '*.log' -exec truncate -s 0 {} + || true
	@echo "Emptying container logs in $(LOG_DIR_APP)…"
	@# Exec only if the app container is running
	@if [ -n "$$(docker compose ps -q app)" ]; then \
		docker compose exec -T app /bin/sh -lc 'mkdir -p "$(LOG_DIR_APP)"; find "$(LOG_DIR_APP)" -maxdepth 1 -type f -name "*.log" -exec truncate -s 0 {} + || true'; \
	else \
		echo "(app container not running — skipped container log cleanup)"; \
	fi
	@echo "Logs emptied."

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

.PHONY: redeploy redeploy-clean redeploy-hard psql show-db-stats clean-logs _start _hard-reset _db-reset-schema _db-apply-schema
