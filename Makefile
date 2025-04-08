export COMPOSE_FILE=deployment/docker-compose.yml:deployment/docker-compose.override.yml
SHELL := /bin/bash

build:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Building in production mode"
	@echo "------------------------------------------------------------------"
	@docker compose build

up:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in production mode"
	@echo "------------------------------------------------------------------"
	@docker compose ${ARGS} up -d nginx django
	@docker compose ${ARGS} up -d --scale worker=${WORKERS:-1} nginx django

dev:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Running in dev mode"
	@echo "------------------------------------------------------------------"
	@docker compose ${ARGS} up -d --scale worker=${WORKERS:-1} dev worker

down:
	@echo
	@echo "------------------------------------------------------------------"
	@echo "Removing production instance!!! "
	@echo "------------------------------------------------------------------"
	@docker compose down