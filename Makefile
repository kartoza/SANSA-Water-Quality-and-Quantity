export COMPOSE_FILE=deployment/docker-compose.yml:deployment/docker-compose.override.yml
SHELL := /bin/bash
WORKERS ?= 1

build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building in production mode"
	@echo "------------------------------------------------------------------"
	@docker compose build

up:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in production mode with $(WORKERS) workers"
	@echo "------------------------------------------------------------------"
	@docker compose ${ARGS} up -d --scale worker=${WORKERS} nginx django

dev:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in dev mode with $(WORKERS) workers"
	@echo "------------------------------------------------------------------"
	@docker compose ${ARGS} up -d --scale worker=${WORKERS} dev worker

down:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Removing production instance!!! "
	@echo "------------------------------------------------------------------"
	@docker compose down