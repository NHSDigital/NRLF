
.EXPORT_ALL_VARIABLES:
.NOTPARALLEL:
.ONESHELL:
.PHONY: *

MAKEFLAGS := --no-print-directory
SHELL := /bin/bash

DIST_PATH ?= ./dist
TEST_ARGS ?= --cov --cov-report=term-missing
FEATURE_TEST_ARGS ?= ./api/tests/integration/features --format progress2
TF_WORKSPACE ?= $(shell terraform -chdir=terraform/infrastructure workspace show)
export PATH := $(PATH):$(PWD)/.venv/bin

default: build

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo
	@echo "where [target] can be:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

asdf-install: ## Install the required tools via ASDF
	@cat .tool-versions | while read tool_version; do \
		tool="$${tool_version% *}"; \
		asdf plugin add "$${tool}"; \
	done
	asdf install

configure: check-warn ## Configure this project repo
	cp scripts/commit-msg.py .git/hooks/prepare-commit-msg && chmod ug+x .git/hooks/*

check: # Check the build environment is setup correctly
	@./scripts/check-build-environment.sh

check-warn:
	@SHOULD_WARN_ONLY=true ./scripts/check-build-environment.sh

build: check-warn build-api-packages build-layers build-dependency-layer ## Build the project

build-dependency-layer:
	@echo "Building Lambda dependency layer"
	@mkdir -p $(DIST_PATH)
	./scripts/build-lambda-dependency-layer.sh $(DIST_PATH)

build-layers: ./layer/*
	@echo "Building Lambda layers"
	@mkdir -p $(DIST_PATH)
	for layer in $^; do \
		[ ! -d "$$layer" ] && continue; \
		./scripts/build-lambda-layer.sh $${layer} $(DIST_PATH); \
	done

build-api-packages: ./api/consumer/* ./api/producer/*
	@echo "Building API packages"
	@mkdir -p $(DIST_PATH)
	for api in $^; do \
		[ ! -d "$$api" ] && continue; \
		./scripts/build-lambda-package.sh $${api} $(DIST_PATH); \
	done

test: check-warn ## Run the unit tests
	@echo "Running unit tests"
	pytest -m "not integration and not legacy and not smoke" --ignore=mi $(TEST_ARGS)

test-integration: check-warn ## Run the integration tests
	@echo "Running integration tests"
	pytest -m "integration and not firehose" $(TEST_ARGS)

test-firehose-integration: check-warn ## Run the firehose integration tests
	@echo "Running firehose integration tests"
	pytest -m "integration and firehose" --runslow $(TEST_ARGS)

test-features: check-warn ## Run the BDD feature tests locally
	@echo "Running feature tests locally"
	behave $(FEATURE_TEST_ARGS)

test-features-integration: check-warn ## Run the BDD feature tests in the integration environment
	@echo "Running feature tests in the integration environment"
	behave --define="integration_test=true" --define="env=$(TF_WORKSPACE)" $(FEATURE_TEST_ARGS)
	allure generate ./allure-results -o ./allure-report --clean
	# allure open ./allure-report

lint: check-warn ## Lint the project
	pre-commit run --all-files

clean: ## Remove all generated and temporary files
	[ -n "$(DIST_PATH)" ] && \
		rm -rf $(DIST_PATH)/*.zip && \
		rmdir $(DIST_PATH) 2>/dev/null || true
