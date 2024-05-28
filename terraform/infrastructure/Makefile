
ENV ?= dev
TF_WORKSPACE_NAME ?= $(shell (whoami || hostname) | head -c 5)-$(ENV)
TF_ARGS ?=
ENV_ACCOUNT_NAME ?= $(shell ../../scripts/get-account-name-for-env.sh $(ENV))
ENV_ACCOUNT_ID ?= $(shell aws secretsmanager get-secret-value --secret-id nhsd-nrlf--mgmt--$(ENV_ACCOUNT_NAME)-account-id --query SecretString --output text)

export ENV ENV_ACCOUNT_NAME

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo
	@echo "where [target] can be:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

check: ## Check the deploy environment is setup correctly
	@(cd ../.. && ./scripts/check-deploy-environment.sh)

check-warn:
	@(cd ../.. && SHOULD_WARN_ONLY=true ./scripts/check-deploy-environment.sh)

build-artifacts: ## Build the NRLF artifacts to deploy
	(cd ../.. && $(MAKE) build)

init: check-warn ## Initialise the Terraform workspace
	-(cd ../.. && $(MAKE) ENV=$(ENV) truststore-pull-server)
	terraform init
	(terraform workspace select $(TF_WORKSPACE_NAME) || terraform workspace new $(TF_WORKSPACE_NAME))

plan: check-warn ## Plan the Terraform changes
	terraform plan \
		-var-file=./etc/$(ENV).tfvars \
		-var 'assume_role_arn=arn:aws:iam::$(ENV_ACCOUNT_ID):role/terraform' \
		$(TF_ARGS)

apply: check-warn ## Apply the Terraform changes
	terraform apply \
		-var-file=./etc/$(ENV).tfvars \
		-var 'assume_role_arn=arn:aws:iam::$(ENV_ACCOUNT_ID):role/terraform' \
		$(TF_ARGS)

destroy: check-warn ## Destroy the Terraform resources
	terraform destroy \
		-var-file=./etc/$(ENV).tfvars \
		-var 'assume_role_arn=arn:aws:iam::$(ENV_ACCOUNT_ID):role/terraform' \
		$(TF_ARGS)
