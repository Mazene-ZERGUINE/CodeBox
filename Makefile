# Usage:
# make dev
# make prod
# make migrate
# make makemigrations app=core
# make install
# make celery
# make flower

SHELL := /bin/bash

PY               ?= python
MANAGE           := $(PY) manage.py
PROJECT          ?= config
HOST             ?= 0.0.0.0
PORT             ?= 8000
WORKERS          ?= 3
TIMEOUT          ?= 60
LOG_LEVEL        ?= info

CELERY            ?= celery
CELERY_APP        ?= codeBox.celery_app
CELERY_LOGLEVEL   ?= INFO
CELERY_CONCURRENCY ?= 4
CELERY_POOL       ?= prefork
CELERY_QUEUES     ?= default
FLOWER_PORT       ?= 5555


DJANGO_SETTINGS_DEV   ?=
DJANGO_SETTINGS_PROD  ?=

define run_with_settings
	@if [ -n "$(1)" ]; then \
		DJANGO_SETTINGS_MODULE=$(1) $(2); \
	else \
		$(2); \
	fi
endef

.PHONY: help install dev prod migrate makemigrations superuser collectstatic shell test clean \
        celery celery-beat flower dev-all

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

install:
	@if [ -f requirements.txt ]; then pip install -r requirements.txt; else echo "No requirements.txt"; fi

dev:
	$(call run_with_settings,$(DJANGO_SETTINGS_DEV),$(MANAGE) runserver $(HOST):$(PORT))

prod:
	@command -v gunicorn >/dev/null 2>&1 || { echo "Gunicorn not found. Install with: pip install gunicorn"; exit 1; }
	$(call run_with_settings,$(DJANGO_SETTINGS_PROD),gunicorn $(PROJECT).wsgi:application \
		--bind $(HOST):$(PORT) \
		--workers $(WORKERS) \
		--timeout $(TIMEOUT) \
		--log-level $(LOG_LEVEL))

migrate:
	$(call run_with_settings,$(DJANGO_SETTINGS_DEV),$(MANAGE) migrate)

makemigrations:
	$(call run_with_settings,$(DJANGO_SETTINGS_DEV),$(MANAGE) makemigrations $(app))

test:
	$(call run_with_settings,$(DJANGO_SETTINGS_DEV),$(MANAGE) test)

clean:
	@find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete 2>/dev/null || true

celery:
	$(call run_with_settings,$(DJANGO_SETTINGS_DEV),$(CELERY) -A $(CELERY_APP) worker \
		-l $(CELERY_LOGLEVEL) -P $(CELERY_POOL) -c $(CELERY_CONCURRENCY) -Q $(CELERY_QUEUES))

flower:
	@command -v flower >/dev/null 2>&1 || { echo "Flower not found. Install with: pip install flower"; exit 1; }
	$(call run_with_settings,$(DJANGO_SETTINGS_DEV),flower -A $(CELERY_APP) --port=$(FLOWER_PORT))
